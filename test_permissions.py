import config
import logging
import asyncio
import discord

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_channel_permissions(channel):
    logger.debug(f"Testing channel permissions for channel {channel.name}")
    try:
        test_message = await channel.send("Test message to verify bot permissions")
        logger.debug("Successfully sent test message")
        await asyncio.sleep(2)  # Wait for 2 seconds
        await test_message.delete()
        logger.debug("Successfully deleted test message")
    except discord.errors.Forbidden:
        logger.error("Bot doesn't have permission to send messages in this channel")
    except Exception as e:
        logger.error(f"An error occurred while testing channel permissions: {e}")