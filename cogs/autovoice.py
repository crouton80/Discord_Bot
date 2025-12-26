"""Auto-join voice channel functionality."""
import discord
from discord.ext import commands
import asyncio
import random
import logging
import yt_dlp
from utils.config import Config

logger = logging.getLogger(__name__)


class AutoVoiceCog(commands.Cog):
    """Handles automatic voice channel joining and music playback."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.join_enabled = True
        self.ffmpeg_path = Config.find_ffmpeg()
    
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """Called when a voice state is updated."""
        if not self.join_enabled:
            return
        
        voice_channel_ids = Config.VOICE_CHANNEL_IDS
        if not voice_channel_ids:
            return
        
        # Get voice channels
        voice_channels = []
        for vc_id in voice_channel_ids:
            channel = self.bot.get_channel(vc_id)
            if channel:
                voice_channels.append(channel)
        
        if not voice_channels:
            logger.warning(f"Voice channel(s) with ID(s) {voice_channel_ids} not found.")
            return
        
        before_channel_id = before.channel.id if before.channel else None
        after_channel_id = after.channel.id if after.channel else None
        logger.debug(f"Member {member} - Before: {before_channel_id}, After: {after_channel_id}")
        
        # Handle bot's own state changes
        if member == self.bot.user:
            await self._handle_bot_voice_state_change(before, after, voice_channels)
            return
        
        # Handle other members joining/leaving
        await self._handle_member_voice_state_change(member, before, after, voice_channels)
    
    async def _handle_bot_voice_state_change(
        self,
        before: discord.VoiceState,
        after: discord.VoiceState,
        voice_channels: list
    ):
        """Handle bot's own voice state changes."""
        before_channel_id = before.channel.id if before.channel else None
        after_channel_id = after.channel.id if after.channel else None
        
        voice_client = discord.utils.get(self.bot.voice_clients, guild=after.guild if after.guild else None)
        monitored_channel_ids = {vc.id for vc in voice_channels}
        before_is_monitored = before_channel_id in monitored_channel_ids if before_channel_id else False
        after_is_monitored = after_channel_id in monitored_channel_ids if after_channel_id else False
        
        # Bot was disconnected
        if before_channel_id and not after_channel_id:
            for voice_channel in voice_channels:
                num_members = len([m for m in voice_channel.members if m != self.bot.user])
                if num_members > 0:
                    logger.info(f"Reconnecting to {voice_channel.name} because members are still present")
                    await asyncio.sleep(1)
                    await self._join_and_play(voice_channel)
                    return
        
        # Bot was moved to a different channel
        elif before_channel_id != after_channel_id:
            if not before_channel_id:
                logger.debug("Bot connected from None - likely a command. Not interfering.")
                return
            
            if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                logger.debug("Bot is playing audio. Not interfering with connection.")
                return
            
            if not after_is_monitored and voice_client:
                logger.info(f"Bot was moved to non-monitored channel {after_channel_id}. Disconnecting...")
                try:
                    await voice_client.disconnect()
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error disconnecting: {e}")
            
            for voice_channel in voice_channels:
                num_members = len([m for m in voice_channel.members if m != self.bot.user])
                if num_members > 0:
                    if voice_client and voice_client.channel and voice_client.channel.id == voice_channel.id:
                        logger.debug(f"Bot is already in {voice_channel.name}")
                        continue
                    logger.info(f"Reconnecting to {voice_channel.name} because members are still present")
                    await asyncio.sleep(1)
                    await self._join_and_play(voice_channel)
                    return
    
    async def _handle_member_voice_state_change(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
        voice_channels: list
    ):
        """Handle member voice state changes."""
        before_channel_id = before.channel.id if before.channel else None
        after_channel_id = after.channel.id if after.channel else None
        
        for voice_channel in voice_channels:
            if voice_channel.id in {before_channel_id, after_channel_id}:
                num_members = len([m for m in voice_channel.members if m != self.bot.user])
                logger.debug(f"Members in {voice_channel.name} (excluding bot): {num_members}")
                voice_client = discord.utils.get(self.bot.voice_clients, guild=member.guild)
                
                if num_members > 0:
                    if voice_client:
                        if voice_client.channel and voice_client.channel.id != voice_channel.id:
                            logger.info(f"Bot is in a different channel. Moving to {voice_channel.name}")
                            await voice_client.disconnect()
                            await self._join_and_play(voice_channel)
                        elif not voice_client.channel:
                            logger.info(f"Bot voice client exists but not in a channel. Connecting to {voice_channel.name}")
                            await self._join_and_play(voice_channel)
                        else:
                            logger.debug(f"Bot is already in the correct channel: {voice_channel.name}")
                    else:
                        logger.info(f"Bot is not connected. Connecting to {voice_channel.name}")
                        await self._join_and_play(voice_channel)
                else:
                    if voice_client and voice_client.channel and voice_client.channel.id == voice_channel.id:
                        logger.info(f"No members left in {voice_channel.name}. Bot should leave.")
                        await voice_client.disconnect()
    
    async def _join_and_play(self, voice_channel: discord.VoiceChannel):
        """Join a voice channel and play a random YouTube video."""
        youtube_urls = Config.YOUTUBE_URLS
        if not youtube_urls:
            logger.warning("No YouTube URLs configured for auto-join")
            return
        
        chosen_video = random.choice(youtube_urls)
        voice_client = None
        
        try:
            # Check for existing voice client
            existing_client = discord.utils.get(self.bot.voice_clients, guild=voice_channel.guild)
            if existing_client:
                if existing_client.is_connected() and existing_client.channel and existing_client.channel.id == voice_channel.id:
                    logger.debug(f"Bot is already connected to {voice_channel.name}. Skipping connection.")
                    return
                elif existing_client.is_connected():
                    logger.info(f"Bot is connected to a different channel. Disconnecting...")
                    try:
                        await existing_client.disconnect()
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Error disconnecting from existing channel: {e}")
                elif not existing_client.is_connected():
                    logger.debug("Cleaning up disconnected voice client")
                    try:
                        await existing_client.disconnect()
                    except Exception:
                        pass
            
            logger.info(f"Attempting to connect to {voice_channel.name}")
            voice_client = await voice_channel.connect()
            logger.info(f"Bot connected to {voice_channel.name}")
            
            # Set options for low quality audio stream
            ydl_opts = {
                'format': 'worstaudio/worst',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '48',
                }],
            }
            
            logger.debug(f"Fetching audio from {chosen_video} with yt-dlp")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(chosen_video, download=False)
                url2 = info['url']
                logger.debug(f"Extracted URL: {url2}")
            
            # Play the audio
            logger.info(f"Playing audio from URL: {url2}")
            source = await discord.FFmpegOpusAudio.from_probe(url2, executable=self.ffmpeg_path)
            voice_client.play(source, after=lambda e: logger.info('Finished playing!' if not e else f'Error: {e}'))
            
            # Wait for the audio to finish
            while voice_client.is_playing():
                await asyncio.sleep(1)
            
            logger.info("Audio playback completed.")
            
            # Check if we should stay connected
            num_members = len([m for m in voice_channel.members if m != self.bot.user])
            if num_members > 0:
                logger.info(f"Members still in {voice_channel.name}. Bot will stay connected.")
                return
        
        except Exception as e:
            logger.error(f"Error during join_and_play: {e}")
        finally:
            # Only disconnect if no members left
            if voice_client and voice_client.is_connected():
                num_members = len([m for m in voice_channel.members if m != self.bot.user])
                if num_members == 0:
                    logger.info(f"No members left in {voice_channel.name}. Disconnecting.")
                    await voice_client.disconnect()
    
    @commands.command(name='stop_bullying')
    async def stop_bullying(self, ctx: commands.Context):
        """Disable auto-join functionality."""
        self.join_enabled = False
        await ctx.send("Gata sefu nu da.")
    
    @commands.command(name='start_bullying')
    async def start_bullying(self, ctx: commands.Context):
        """Enable auto-join functionality."""
        self.join_enabled = True
        await ctx.send("Va omor, SOBOLANILOR!")


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(AutoVoiceCog(bot))

