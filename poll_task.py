import discord
import asyncio
from discord.ext import tasks
import trivia_api
import roles_management
import config
import html
import logging
import test_permissions
import youtube

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@tasks.loop(hours=1)
async def daily_poll(bot):
    logger.debug("Starting daily_poll")
    
    for channel_id in config.CHANNEL_ID:
        channel = bot.get_channel(channel_id)
        
        if channel is None:
            logger.error(f"Channel with ID {channel_id} not found.")
            continue

        #UNCOMMENT THIS WHEn DEBUGGING
        # await test_permissions.test_channel_permissions(channel)

        # Fetch a poll question from trivia API
        question_data = trivia_api.fetch_question()
        question = html.unescape(question_data['question'])
        correct_answer = html.unescape(question_data['correct_answer'])
        all_answers = [html.unescape(answer) for answer in question_data['all_answers']] 

        # Post the question in the channel
        poll_message = await channel.send(roles_management.construct_poll_message(question, all_answers))
        logger.debug("Poll message sent")

        # React with answers so users may answer the poll
        await roles_management.add_reactions(poll_message, all_answers)
        logger.debug("Reactions added to poll message")

        # Wait for response (30 minutes)
        logger.debug(f"Waiting for {config.TIME_LIMIT_SECONDS} seconds")
        await asyncio.sleep(config.TIME_LIMIT_SECONDS)
        logger.debug("Wait time completed")

        # Fetch reactions and manage roles for correct/incorrect answers
        logger.debug("Starting to process poll results")

        # Fetch the message again to ensure we have the latest reactions
        poll_message = await channel.fetch_message(poll_message.id)
        logger.debug(f"Fetched poll message. Reactions: {[r.emoji for r in poll_message.reactions]}")

        await roles_management.process_poll_results(poll_message, all_answers, correct_answer, bot, channel)
        logger.debug("Finished processing poll results")

        await channel.send("S-a terminat sondajul.")
        await channel.send("https://media.tenor.com/PJ2vgGk8bWoAAAAM/itsover-wojack.gif")
        logger.debug("Daily poll completed")

        time.sleep(10)

def start_daily_poll(bot):
    logger.info("Starting daily poll task")
    daily_poll.start(bot)