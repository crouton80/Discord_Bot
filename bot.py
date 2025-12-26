"""Main Discord bot file."""
import discord
from discord.ext import commands
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import Config
from utils.logger import setup_logging

# Setup logging
logger = setup_logging()

# Configure intents
intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.presences = True
intents.voice_states = True

# Create bot instance
bot = commands.Bot(
    command_prefix=Config.COMMAND_PREFIX,
    intents=intents
)


async def load_extensions():
    """Load all bot extensions (cogs)."""
    extensions = [
        'cogs.events',
        'cogs.autovoice',
        'cogs.youtube',
        'cogs.admin',
    ]
    
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f"Loaded extension: {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension {extension}: {e}")


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f"Bot is ready! Logged in as {bot.user}")
    logger.info(f"Bot ID: {bot.user.id}")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")
    # Note: Background tasks are started in cogs/events.py on_ready handler


async def setup_bot():
    """Setup the bot before starting."""
    # Load configuration from config.py (if it exists)
    Config.load_from_file("config.py")
    
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed. Please check your configuration.")
        return False
    
    # Load all extensions
    await load_extensions()
    return True


def run_bot():
    """Run the bot (entry point)."""
    # Setup bot asynchronously
    if not asyncio.run(setup_bot()):
        return
    
    # Start the bot (this blocks until the bot is closed)
    try:
        bot.run(Config.BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")


if __name__ == "__main__":
    run_bot()
