"""Admin commands for managing bot features."""
import discord
from discord.ext import commands
import logging
import poll_task
import meme_task
from utils.config import Config

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog):
    """Administrative commands for toggling bot features."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='toggle_polls')
    async def toggle_polls(self, ctx: commands.Context):
        """Toggle daily trivia polls on/off."""
        new_value = not Config.get_setting("polls_enabled")
        Config.set_setting("polls_enabled", new_value)
        
        # Start/stop the task immediately
        try:
            if new_value:
                if not poll_task.daily_poll.is_running():
                    poll_task.daily_poll.start(self.bot)
            else:
                if poll_task.daily_poll.is_running():
                    poll_task.daily_poll.stop()
        except Exception as e:
            logger.error(f"Error toggling daily_poll task: {e}")
        
        await ctx.send(f"Poll posting now {'ON' if new_value else 'OFF'}.")
    
    @commands.command(name='toggle_9gag')
    async def toggle_9gag(self, ctx: commands.Context):
        """Toggle 9GAG meme posting on/off."""
        new_value = not Config.get_setting("9gag_enabled")
        Config.set_setting("9gag_enabled", new_value)
        
        # Start/stop the task immediately
        try:
            if new_value:
                if not meme_task.post_meme.is_running():
                    meme_task.post_meme.start(self.bot)
            else:
                if meme_task.post_meme.is_running():
                    meme_task.post_meme.stop()
        except Exception as e:
            logger.error(f"Error toggling 9GAG task: {e}")
        
        await ctx.send(f"9GAG memes now {'ON' if new_value else 'OFF'}.")


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(AdminCog(bot))

