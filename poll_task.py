import discord
import asyncio
from discord.ext import tasks
import trivia_api
import roles_management
import config
import html

@tasks.loop(minutes=35)
async def daily_poll(bot):
    channel = bot.get_channel(config.CHANNEL_ID)
    
    # Fetch a poll question from trivia API
    question_data = trivia_api.fetch_question()
    question = html.unescape(question_data['question'])
    correct_answer = html.unescape(question_data['correct_answer'])
    all_answers = [html.unescape(answer) for answer in question_data['all_answers']] 

    # Post the question in the channel
    poll_message = await channel.send(roles_management.construct_poll_message(question, all_answers))

    #React with answers so users may answer the poll
    await roles_management.add_reactions(poll_message, all_answers)

    # Wait for response (30 minutes)
    await asyncio.sleep(config.TIME_LIMIT_SECONDS)

    # Fetch reactions and manage roles for correct/incorrect answers
    await roles_management.process_poll_results(poll_message, all_answers, correct_answer, bot)


def start_daily_poll(bot):
    daily_poll.start(bot)