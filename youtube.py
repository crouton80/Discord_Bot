import asyncio
import discord
from discord.ext import commands
import yt_dlp
import logging
import os
from collections import defaultdict

# Set working directory to user's home directory
# os.chdir(os.path.expanduser("~"))

# Initialize logger for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('yt_dlp')
logger.setLevel(logging.DEBUG)

banned_users = [330710707010142209]

# FFmpeg path for Windows - with fallback
FFMPEG_PATH = r"C:\Users\alaric\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe"

# Fallback: if the specific path doesn't exist, try to find ffmpeg in PATH
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"  # Let discord.py find it in PATH

FFMPEG_OPTIONS = {
    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -y",
    "options": "-vn -b:a 128k -ac 2 -ar 48000",
}

@commands.command(name='join')
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not connected to a voice channel.")
        return
    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)

@commands.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

@commands.command(name='pause')
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Playback paused.")

@commands.command(name='resume')
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Playback resumed.")

@commands.command(name='stop')
async def stop(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")


class YouTubeCog(commands.Cog):
    logger.debug("Loading YoutubeCog...")

    def __init__(self, bot):
        self.bot = bot
        self._join_locks = defaultdict(asyncio.Lock)  # debounces parallel connects

    # ---- helper: connect/move without re-invoking commands ----
    async def _ensure_connected(self, ctx: commands.Context, *, timeout: float = 20.0) -> discord.VoiceClient | None:
        if not ctx.author or not getattr(ctx.author, "voice", None) or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel.")
            return None

        target: discord.VoiceChannel = ctx.author.voice.channel # 

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

    # ---- your existing helper, but using the safe connector above ----
    async def play_audio(self, ctx, search: str):
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
            "verbose": True,
            "cookies": r"C:\Users\Lorgar\Downloads\cookies.txt",
            "socket_timeout": 30,  # Increase timeout
            "extract_flat": False,
            "no_warnings": False,
            "prefer_ffmpeg": True,
            "extractors_args": {
                "youtube": {
                    "player_client": ["web", "android", "mweb"],  # Added mweb for broader compatibility
                    "formats": ["missing_pot"]  # Allow formats without PO token
                }
            },
            "format_sort": ["ext:webm", "ext:mp4:m4a", "ext:mp3", "acodec:opus", "acodec:mp4a", "acodec:vorbis"],
            "format_sort_force": True,
            "prefer_insecure": False,  # Prefer secure connections
        }

        try:
            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search, download=False)
                    return info["entries"][0] if "entries" in info else info

            # run the blocking extract in a thread
            info = await asyncio.get_running_loop().run_in_executor(None, _extract)
            url = info["url"]
            title = info.get("title", "Unknown Title")
            
            logger.debug(f"FFmpeg path: {FFMPEG_PATH}")
            logger.debug(f"Audio URL: {url}")
            
            # stop current audio if any
            if vc.is_playing() or vc.is_paused():
                vc.stop()

            # Try multiple audio source creation methods with better error handling
            source = None
            
            # Method 1: Try FFmpegOpusAudio with Windows-optimized options
            try:
                logger.debug("Attempting to create FFmpegOpusAudio with Windows options...")
                windows_options = {
                    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -y",
                    "options": "-vn -b:a 128k -ac 2 -ar 48000 -f opus"
                }
                source = discord.FFmpegOpusAudio(url, executable=FFMPEG_PATH, **windows_options)
                logger.debug("FFmpegOpusAudio with Windows options created successfully")
            except Exception as e:
                logger.error(f"FFmpegOpusAudio with Windows options failed: {e}")
                
                # Method 2: Try FFmpegOpusAudio with simplified options
                try:
                    logger.debug("Attempting FFmpegOpusAudio with simplified options...")
                    simple_options = {
                        "before_options": "-nostdin -y",
                        "options": "-vn -b:a 128k -f opus"
                    }
                    source = discord.FFmpegOpusAudio(url, executable=FFMPEG_PATH, **simple_options)
                    logger.debug("FFmpegOpusAudio with simple options created successfully")
                except Exception as e2:
                    logger.error(f"FFmpegOpusAudio with simple options failed: {e2}")
                    
                    # Method 3: Try FFmpegPCMAudio
                    try:
                        logger.debug("Falling back to FFmpegPCMAudio...")
                        pcm_options = {
                            "before_options": "-nostdin -y",
                            "options": "-vn -b:a 128k -ac 2 -ar 48000"
                        }
                        source = discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **pcm_options)
                        logger.debug("FFmpegPCMAudio created successfully")
                    except Exception as e3:
                        logger.error(f"FFmpegPCMAudio also failed: {e3}")
                        
                        # Method 4: Try with just the URL and let discord.py handle it
                        try:
                            logger.debug("Attempting to create audio source from URL directly...")
                            source = await discord.FFmpegOpusAudio.from_probe(url, executable=FFMPEG_PATH)
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
                        
                except Exception as play_error:
                    logger.error(f"Error during playback: {play_error}")
                    await ctx.send("❌ Error during playback. Please try a different video.")
            else:
                await ctx.send("Failed to create audio source. Please try a different video.")
        except Exception as e:
            logger.error(f"Error while playing audio: {e}")
            await ctx.send("An error occurred while trying to play the audio.")

    # ---- commands (no calling commands from commands) ----

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, extension: str):
        await ctx.bot.reload_extension(extension)
        await ctx.send(f"Reloaded `{extension}` successfully.")

    @commands.command(name="join")
    async def join(self, ctx):
        vc = await self._ensure_connected(ctx)
        if vc:
            await logger.debug(f"Joined **{vc.channel.name}**.")

    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.command(name="pause")
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send("Paused ⏸️")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send("Resumed ▶️")
        else:
            await ctx.send("Nothing to resume.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await ctx.send("Stopped ⏹️")
        else:
            await ctx.send("Nothing to stop.")

    @commands.command(name="play")
    async def play(self, ctx, *, search: str):
        # Keep your banned list usage, but make it safe if it's not defined
        banned = globals().get("banned_users", set())
        if ctx.author.id in banned:
            await ctx.send("Taci dreq.")
            return
        await self.play_audio(ctx, search)
        
    @commands.command(name="test_voice")
    async def test_voice(self, ctx):
        """Test voice connection"""
        vc = await self._ensure_connected(ctx)
        if vc:
            await ctx.send(f"✅ Voice connection test successful! Connected to {vc.channel.name}")
        else:
            await ctx.send("❌ Voice connection test failed!")
            
    @commands.command(name="test_audio")
    async def test_audio(self, ctx):
        """Test audio with a simple video"""
        await self.play_audio(ctx, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")



async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
