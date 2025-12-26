"""YouTube music playback cog."""
import asyncio
import time
import discord
from discord.ext import commands
import yt_dlp
import logging
import os
import re
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
from utils.config import Config

logger = logging.getLogger(__name__)

# Banned users list
BANNED_USERS = [330710707010142209]

# FFmpeg path
FFMPEG_PATH = Config.find_ffmpeg()

FFMPEG_OPTIONS = {
    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -y",
    "options": "-vn -b:a 128k -ac 2 -ar 48000",
}


class YouTubeCog(commands.Cog):
    """YouTube music playback functionality."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._join_locks = defaultdict(asyncio.Lock)  # debounces parallel connects
        # Simple per-guild playback state for seeking
        # keys: query (str), base (int seconds), started_at (monotonic), paused (bool), paused_at (monotonic|None), duration (int|None)
        self._playback: dict[int, dict] = {}
    
    async def _ensure_connected(self, ctx: commands.Context, *, timeout: float = 20.0) -> discord.VoiceClient | None:
        """Ensure bot is connected to the user's voice channel."""
        if not ctx.author or not getattr(ctx.author, "voice", None) or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel.")
            return None
        
        target: discord.VoiceChannel = ctx.author.voice.channel
        
        async with self._join_locks[ctx.guild.id]:
            vc: discord.VoiceClient | None = ctx.voice_client
            
            # Check for multiple voice clients (potential conflict)
            all_voice_clients = ctx.guild.voice_channels
            connected_clients = [client for client in ctx.bot.voice_clients if client.guild == ctx.guild]
            
            if len(connected_clients) > 1:
                logger.warning(f"Multiple voice clients detected: {len(connected_clients)}")
                # Disconnect all except the one we want
                for client in connected_clients:
                    if client != vc:
                        await client.disconnect(force=True)
                        logger.info(f"Disconnected conflicting voice client from {client.channel.name}")
            
            try:
                if vc and vc.channel and vc.channel.id == target.id:
                    return vc
                if vc and vc.channel and vc.channel.id != target.id:
                    await vc.move_to(target, timeout=timeout)
                    return vc
                # not connected
                vc = await target.connect(timeout=timeout, reconnect=True, self_deaf=False)
                return vc
            except asyncio.TimeoutError:
                await ctx.send("I couldn't connect to voice in time. Try again in a few seconds.")
                return None
    
    def _parse_time_to_seconds(self, text: str) -> int | None:
        """Parse a timestamp like 90, 1:30, 01:02:03, or 1h2m3s into seconds."""
        if not text:
            return None
        text = text.strip().lower()
        # 1) Plain integer seconds
        if text.isdigit():
            return int(text)
        # 2) hh:mm[:ss] format
        if ":" in text:
            parts = text.split(":")
            try:
                parts = [int(p) for p in parts]
            except ValueError:
                parts = []
            if len(parts) == 3:
                h, m, s = parts
                return h * 3600 + m * 60 + s
            if len(parts) == 2:
                m, s = parts
                return m * 60 + s
        # 3) 1h2m3s style
        m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", text)
        if m:
            h = int(m.group(1) or 0)
            mn = int(m.group(2) or 0)
            s = int(m.group(3) or 0)
            total = h * 3600 + mn * 60 + s
            return total if total > 0 else None
        return None
    
    def _extract_start_from_query(self, query: str) -> tuple[str, int | None]:
        """Extract --start <time> from free text or t/start param from a URL. Returns (clean_query, seconds)."""
        start_seconds: int | None = None
        cleaned = query
        
        # --start <time>
        m = re.search(r"\s--start\s+(\S+)", cleaned)
        if m:
            ts = m.group(1)
            ss = self._parse_time_to_seconds(ts)
            if ss is not None:
                start_seconds = ss
            cleaned = cleaned[:m.start()] + cleaned[m.end():]
        
        # If it's a URL, also respect t= or start= query param
        try:
            u = urlparse(cleaned.strip())
            if u.scheme in ("http", "https") and u.netloc:
                qs = parse_qs(u.query)
                t_param = None
                if "t" in qs:
                    t_param = qs["t"][0]
                elif "start" in qs:
                    t_param = qs["start"][0]
                # also support timestamp in fragment (e.g., youtu.be/...#t=1m30s)
                if not t_param and u.fragment:
                    frag_qs = parse_qs(u.fragment)
                    if "t" in frag_qs:
                        t_param = frag_qs["t"][0]
                if t_param and start_seconds is None:
                    # YouTube may provide like 90 or 1m30s
                    ss = self._parse_time_to_seconds(t_param)
                    if ss is not None:
                        start_seconds = ss
        except Exception:
            pass
        
        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned, start_seconds
    
    def _ffmpeg_opts_with_seek(self, seconds: int | None, *, format_flag: str | None = None) -> tuple[dict, dict]:
        """Build before_options/options dicts, injecting -ss if provided."""
        before = "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -y"
        if seconds is not None and seconds >= 0:
            before = f"-nostdin -ss {seconds} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -y"
        # Common audio encoding/display options
        opts = "-vn -b:a 128k -ac 2 -ar 48000"
        if format_flag == "opus":
            opts += " -f opus"
        return {"before_options": before}, {"options": opts}
    
    async def play_audio(self, ctx, search: str):
        """Play audio from YouTube URL or search query."""
        # Parse optional start time
        original_query = search
        search, start_at = self._extract_start_from_query(search)
        vc = await self._ensure_connected(ctx)
        if not vc:
            return
        
        # Ensure voice client is ready
        if not vc.is_connected():
            await ctx.send("❌ Voice client is not connected properly.")
            return
        
        # Search for the YouTube video with improved options - allow m3u8 as fallback
        ydl_opts = {
            "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=?720]",
            "noplaylist": True,
            "quiet": False,
            "default_search": "ytsearch1",
            "verbose": False,  # Reduce verbosity to avoid spam
            "socket_timeout": 30,
            "extract_flat": False,
            "no_warnings": False,
            "prefer_ffmpeg": True,
            "extractors_args": {
                "youtube": {
                    "player_client": ["android", "web", "mweb"],  # Try android first for better compatibility
                    "formats": ["missing_pot"]  # Allow formats without PO token
                }
            },
            "format_sort": ["ext:webm", "ext:mp4:m4a", "ext:mp3", "acodec:opus", "acodec:mp4a", "acodec:vorbis"],
            "format_sort_force": True,
            "prefer_insecure": False,
            "nocheckcertificate": False,
            "ignoreerrors": False,
            "no_check_certificate": False,
        }
        
        # Add cookies if file exists (optional)
        cookies_path = r"C:\Users\Lorgar\Downloads\cookies.txt"
        if os.path.exists(cookies_path):
            ydl_opts["cookies"] = cookies_path
        
        try:
            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search, download=False)
                    return info["entries"][0] if "entries" in info else info
            
            # run the blocking extract in a thread
            info = await asyncio.get_running_loop().run_in_executor(None, _extract)
            
            # Validate that we got a valid URL
            url = info.get("url")
            if not url:
                logger.error("Failed to extract audio URL from video")
                await ctx.send("❌ Failed to extract audio URL. The video might be unavailable or restricted.")
                return
            
            # Check if URL is a file path (shouldn't happen with download=False, but check anyway)
            if os.path.exists(url) or (not url.startswith(("http://", "https://")) and (url.startswith(("tmp", "temp")) or "\\" in url or "/" in url and not url.startswith("http"))):
                logger.error(f"yt-dlp returned a file path instead of URL: {url}")
                await ctx.send("❌ Error: Video extraction returned invalid format. Please try a different video.")
                return
            
            # Ensure URL is a valid HTTP/HTTPS URL
            if not url.startswith(("http://", "https://")):
                logger.error(f"Invalid URL format: {url}")
                await ctx.send("❌ Error: Invalid audio stream URL. Please try a different video.")
                return
            
            title = info.get("title", "Unknown Title")
            duration = info.get("duration")  # seconds or None
            # Prefer a canonical page URL to allow re-extraction on seek
            page_url = info.get("webpage_url") or info.get("original_url") or search
            
            logger.debug(f"FFmpeg path: {FFMPEG_PATH}")
            logger.debug(f"Audio URL: {url[:100]}...")  # Log first 100 chars to avoid logging full URLs
            
            # stop current audio if any
            if vc.is_playing() or vc.is_paused():
                vc.stop()
            
            # Try multiple audio source creation methods with better error handling
            source = None
            
            # Method 1: Try FFmpegOpusAudio with Windows-optimized options
            try:
                logger.debug("Attempting to create FFmpegOpusAudio with Windows options...")
                before, opts = self._ffmpeg_opts_with_seek(start_at, format_flag="opus")
                windows_options = {**before, **opts}
                source = discord.FFmpegOpusAudio(url, executable=FFMPEG_PATH, **windows_options)
                logger.debug("FFmpegOpusAudio with Windows options created successfully")
            except Exception as e:
                logger.error(f"FFmpegOpusAudio with Windows options failed: {e}")
                
                # Method 2: Try FFmpegOpusAudio with simplified options
                try:
                    logger.debug("Attempting FFmpegOpusAudio with simplified options...")
                    before, opts = self._ffmpeg_opts_with_seek(start_at, format_flag="opus")
                    simple_before = "-nostdin -y"
                    if start_at is not None:
                        simple_before = f"-nostdin -ss {start_at} -y"
                    simple_options = {"before_options": simple_before, **opts}
                    source = discord.FFmpegOpusAudio(url, executable=FFMPEG_PATH, **simple_options)
                    logger.debug("FFmpegOpusAudio with simple options created successfully")
                except Exception as e2:
                    logger.error(f"FFmpegOpusAudio with simple options failed: {e2}")
                    
                    # Method 3: Try FFmpegPCMAudio
                    try:
                        logger.debug("Falling back to FFmpegPCMAudio...")
                        before, opts = self._ffmpeg_opts_with_seek(start_at)
                        simple_before = "-nostdin -y"
                        if start_at is not None:
                            simple_before = f"-nostdin -ss {start_at} -y"
                        pcm_options = {"before_options": simple_before, **opts}
                        source = discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **pcm_options)
                        logger.debug("FFmpegPCMAudio created successfully")
                    except Exception as e3:
                        logger.error(f"FFmpegPCMAudio also failed: {e3}")
                        
                        # Method 4: Try with just the URL and let discord.py handle it
                        try:
                            logger.debug("Attempting to create audio source from URL directly...")
                            before, opts = self._ffmpeg_opts_with_seek(start_at, format_flag="opus")
                            source = await discord.FFmpegOpusAudio.from_probe(
                                url,
                                executable=FFMPEG_PATH,
                                **before,
                                **opts,
                            )
                            logger.debug("FFmpegOpusAudio.from_probe created successfully")
                        except Exception as e4:
                            logger.error(f"All audio source creation methods failed: {e4}")
                            await ctx.send("Failed to process audio stream. Please try a different video.")
                            return
            
            if source:
                try:
                    # Ensure voice client is still connected
                    if not vc.is_connected():
                        await ctx.send("❌ Voice client disconnected. Please try again.")
                        return
                    
                    vc.play(source, after=lambda e: logger.info("Finished playing!" if not e else f"Error after play: {e}"))
                    await ctx.send(f"Now playing **{title}**")
                    
                    # Wait a bit to ensure playback starts
                    await asyncio.sleep(2)
                    
                    # Check if playback actually started and voice client is still connected
                    if not vc.is_connected():
                        await ctx.send("❌ Voice client disconnected during playback.")
                        return
                    elif not vc.is_playing():
                        await ctx.send("❌ Playback failed to start. Please try again.")
                        return
                    else:
                        logger.info("Playback started successfully!")
                        # Record playback state for seeking
                        self._playback[ctx.guild.id] = {
                            "query": page_url,
                            "base": int(start_at or 0),
                            "started_at": time.monotonic(),
                            "paused": False,
                            "paused_at": None,
                            "duration": int(duration) if isinstance(duration, (int, float)) else None,
                            "title": title,
                        }
                        
                except Exception as play_error:
                    logger.error(f"Error during playback: {play_error}")
                    await ctx.send("❌ Error during playback. Please try a different video.")
            else:
                await ctx.send("Failed to create audio source. Please try a different video.")
        except Exception as e:
            logger.error(f"Error while playing audio: {e}")
            await ctx.send("An error occurred while trying to play the audio.")
    
    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, extension: str):
        """Reload a bot extension."""
        await ctx.bot.reload_extension(extension)
        await ctx.send(f"Reloaded `{extension}` successfully.")
    
    @commands.command(name="join")
    async def join(self, ctx):
        """Join the user's voice channel."""
        vc = await self._ensure_connected(ctx)
        if vc:
            await ctx.send(f"Joined **{vc.channel.name}**.")
    
    @commands.command(name="leave")
    async def leave(self, ctx):
        """Leave the current voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not in a voice channel.")
    
    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pause the current playback."""
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            st = self._playback.get(ctx.guild.id)
            if st and not st.get("paused"):
                st["paused"] = True
                st["paused_at"] = time.monotonic()
            await ctx.send("Paused ⏸️")
        else:
            await ctx.send("Nothing is playing.")
    
    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resume paused playback."""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            st = self._playback.get(ctx.guild.id)
            if st and st.get("paused"):
                now = time.monotonic()
                paused_at = st.get("paused_at") or now
                # shift started_at forward by pause duration
                st["started_at"] = st.get("started_at", now) + (now - paused_at)
                st["paused"] = False
                st["paused_at"] = None
            await ctx.send("Resumed ▶️")
        else:
            await ctx.send("Nothing to resume.")
    
    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop the current playback."""
        vc = ctx.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            # Clear playback state
            self._playback.pop(ctx.guild.id, None)
            await ctx.send("Stopped ⏹️")
        else:
            await ctx.send("Nothing to stop.")
    
    @commands.command(name="play")
    async def play(self, ctx, *, search: str):
        """Play audio from YouTube URL or search query."""
        if ctx.author.id in BANNED_USERS:
            await ctx.send("Taci dreq.")
            return
        await self.play_audio(ctx, search)
    
    @commands.command(name="test_voice")
    async def test_voice(self, ctx):
        """Test voice connection."""
        vc = await self._ensure_connected(ctx)
        if vc:
            await ctx.send(f"✅ Voice connection test successful! Connected to {vc.channel.name}")
        else:
            await ctx.send("❌ Voice connection test failed!")
    
    @commands.command(name="test_audio")
    async def test_audio(self, ctx):
        """Test audio with a simple video."""
        await self.play_audio(ctx, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    def _format_ts(self, s: int) -> str:
        """Format seconds as timestamp string."""
        s = max(0, int(s))
        h, rem = divmod(s, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    
    def _current_position(self, guild_id: int) -> int | None:
        """Get current playback position in seconds."""
        st = self._playback.get(guild_id)
        if not st:
            return None
        base = int(st.get("base", 0))
        if st.get("paused"):
            started = st.get("started_at") or time.monotonic()
            paused_at = st.get("paused_at") or started
            elapsed = max(0, paused_at - started)
        else:
            started = st.get("started_at") or time.monotonic()
            elapsed = max(0, time.monotonic() - started)
        pos = base + int(elapsed)
        dur = st.get("duration")
        if isinstance(dur, int):
            pos = min(pos, max(0, dur - 1))
        return max(0, pos)
    
    async def _restart_at(self, ctx: commands.Context, target_seconds: int):
        """Restart playback at a specific time."""
        st = self._playback.get(ctx.guild.id)
        if not st:
            await ctx.send("No track to seek in.")
            return
        query = st.get("query")
        if not query:
            await ctx.send("Cannot seek: missing source info.")
            return
        # Clamp to duration if known
        dur = st.get("duration")
        if isinstance(dur, int):
            target_seconds = max(0, min(int(target_seconds), max(0, dur - 1)))
        else:
            target_seconds = max(0, int(target_seconds))
        
        # Restart playback using the stored query and new start time
        await self.play_audio(ctx, f"{query} --start {target_seconds}")
    
    @commands.command(name="seek")
    async def seek_cmd(self, ctx: commands.Context, *, time_spec: str):
        """Seek to or by time. Examples: seek +10, seek -5, seek 1:23"""
        time_spec = time_spec.strip()
        if not time_spec:
            await ctx.send("Boss, Usage: seek [+/-]seconds | mm:ss | hh:mm:ss")
            return
        current = self._current_position(ctx.guild.id)
        if current is None:
            await ctx.send("Nothing is playing.")
            return
        # Relative seek
        if time_spec.startswith(("+", "-")):
            sign = 1 if time_spec[0] == "+" else -1
            amount = self._parse_time_to_seconds(time_spec[1:])
            if amount is None:
                await ctx.send("Invalid time amount.")
                return
            target = current + sign * amount
        else:
            # Absolute position
            abs_pos = self._parse_time_to_seconds(time_spec)
            if abs_pos is None:
                await ctx.send("Invalid time format.")
                return
            target = abs_pos
        await self._restart_at(ctx, int(target))
        await ctx.send(f"⏩ Moved to {self._format_ts(int(target))}")
    
    @commands.command(name="forward")
    async def forward_cmd(self, ctx: commands.Context, *, amount: str):
        """Forward playback by specified time."""
        secs = self._parse_time_to_seconds(amount)
        if secs is None:
            await ctx.send("Usage: forward <seconds|mm:ss|hh:mm:ss>")
            return
        current = self._current_position(ctx.guild.id)
        if current is None:
            await ctx.send("Nothing is playing.")
            return
        target = current + secs
        await self._restart_at(ctx, int(target))
        await ctx.send(f"⏭️ Forward to {self._format_ts(int(target))}")
    
    @commands.command(name="back", aliases=["backward"])
    async def back_cmd(self, ctx: commands.Context, *, amount: str):
        """Rewind playback by specified time."""
        secs = self._parse_time_to_seconds(amount)
        if secs is None:
            await ctx.send("Usage: back <seconds|mm:ss|hh:mm:ss>")
            return
        current = self._current_position(ctx.guild.id)
        if current is None:
            await ctx.send("Nothing is playing.")
            return
        target = current - secs
        await self._restart_at(ctx, int(target))
        await ctx.send(f"⏮️ Back to {self._format_ts(int(target))}")


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(YouTubeCog(bot))

