import discord
from discord.ext import commands
import yt_dlp
import logging
import os

# Set working directory to user's home directory
# os.chdir(os.path.expanduser("~"))

# Initialize logger for debugging (configured in main entrypoint)
logger = logging.getLogger('yt_dlp')

banned_users = [330710707010142209]

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

        # Helper method to search and play audio
    async def play_audio(self, ctx, search: str):
        # Check if user is in a voice channel
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in a voice channel to play music.")
            return

        # Retrieve the voice client for the guild or connect if not already connected
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client is None:
            voice_client = await ctx.author.voice.channel.connect()
        elif voice_client.channel != ctx.author.voice.channel:
            await voice_client.move_to(ctx.author.voice.channel)

        # Search for the YouTube video with these options
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': 'True',
            'quiet': False,
            'default_search': 'ytsearch1',
            'verbose': True,
            # Prefer cookies from browser; fall back to no auth
            'cookiesfrombrowser': ('chrome', None, None, None)
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search, download=False)
                if 'entries' in info:
                    info = info['entries'][0]  # Get the first result
                url = info['url']
                title = info.get('title', 'Unknown Title')

            # Prepare the FFmpeg source and play it
            source = await discord.FFmpegOpusAudio.from_probe(url)
            if voice_client.is_playing():
                voice_client.stop()  # Stop any current playing audio

            voice_client.play(source, after=lambda e: logger.info('Finished playing!'))

            await ctx.send(f"Now playing **{title}**")
        except Exception as e:
            logger.error(f"Error while playing audio: {e}")
            await ctx.send("An error occurred while trying to play the audio.")


    @commands.command(name='reload')
    async def reload(self, ctx, extension):
        await ctx.bot.reload_extension(extension)
        await ctx.send(f"Reloaded {extension} successfully.")


    @commands.command(name='join')
    async def join(self, ctx):
        await join(ctx)

    @commands.command(name='leave')
    async def leave(self, ctx):
        await leave(ctx)


    @commands.command(name='pause')
    async def pause(self, ctx):
        await pause(ctx)

    @commands.command(name='resume')
    async def resume(self, ctx):
        await resume(ctx)

    @commands.command(name='stop')
    async def stop(self, ctx):
        await stop(ctx)

    @commands.command(name='play')
    async def play(self, ctx, *, search: str):
        #Check if user is in banned list
        if ctx.author.id in banned_users:
            await ctx.send("Taci dreq.")
            return
        await self.play_audio(ctx, search)





async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
