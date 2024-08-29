import discord
import config
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']


def construct_poll_message(question, all_answers):
    poll_message = f"**Ia sa vedem mai ai neuroni?**\n\n{question}\n"
    for i, answer in enumerate(all_answers):
        poll_message += f"{i+1}. {answer}\n"
    return poll_message

async def add_reactions(poll_message, all_answers):
    for i in range(len(all_answers)):
        await poll_message.add_reaction(reactions[i])

async def process_poll_results(message, all_answers, correct_answer, bot, channel):
    logger.debug("Starting process_poll_results")

    # Log information about the message
    logger.debug(f"Message ID: {message.id}")
    logger.debug(f"Message content: {message.content}")
    logger.debug(f"Message type: {type(message)}")

    #Check if message.reactions exists and is iterable
    if not hasattr(message, 'reactions'):
        logger.error("Message object does not have 'reactions' attribute")
        error_message = await channel.send("Error: Unable to process reactions.")
        await asyncio.sleep(4)
        await error_message.delete()
        logger.debug("Deleted error message from chat.")
        return
    
    #Check if message.reactions is list or tuple
    if not isinstance(message.reactions, (list, tuple)):
        logger.error(f"message.reactions is not iterable. Type: {type(message.reactions)}")
        return
    
    #Log the number of reactions
    logger.debug(f"Number of reactions: {len(message.reactions)}")

    # If there are no reactions, log this information
    if len(message.reactions) == 0:
        logger.warning("No reactions found on the message")
        return

    try:
        users_answered = set()
        for reaction in message.reactions:
            logger.debug(f"Processing reaction: {reaction.emoji}")

            if reaction.emoji in reactions:
                async for user in reaction.users():
                    if user == bot.user:
                        continue  # Skip bot's own reaction
                    
                    if user.id in users_answered:
                        continue  # Skip already processed users
                    
                    selected_answer_index = reactions.index(reaction.emoji)
                    selected_answer = all_answers[selected_answer_index]
                    users_answered.add(user.id)

                    member = message.guild.get_member(user.id)
                    incorrect_role = message.guild.get_role(config.INCORRECT_ROLE_ID)

                    if not member:
                        logger.warning(f"Member {user.name} not found in the guild.")
                        continue

                    if not incorrect_role:
                        logger.warning(f"Role with ID {config.INCORRECT_ROLE_ID} not found.")
                        continue

                    logger.debug(f"User {user.name} chose the answer: {selected_answer}")

                    if selected_answer == correct_answer:
                        logger.debug(f"{user.name} chose the correct answer.")
                        if incorrect_role in member.roles:
                            try:
                                await member.remove_roles(incorrect_role)
                                logger.debug(f"Removed incorrect role from {user.name}.")
                                await channel.send(f"{user.mention} Hai vere ca ai trecut cu 5-ul de doamne ajuta. Ai 5 clase acuma.")
                            except Exception as e:
                                logger.error(f"Failed to remove incorrect role from {user.name}: {e}")
                        else:
                            await channel.send(f"{user.mention} ai vazut, ce usor a fost? ehe")
                    else:
                        logger.debug(f"{user.name} answered incorrectly.")
                        await assign_incorrect_role(message, user, channel)

    except Exception as e:
        logger.error(f"Error during process_poll_results: {e}")
        await channel.send(f"Error occurred: {e}")

    logger.debug("Finished processing individual responses.")
    
    await assign_roles_to_non_participants(message, users_answered)
    logger.debug("Finished assign_roles_to_non_participants")



async def assign_incorrect_role(message, user, channel):
    logger.debug(f"Assigning incorrect role to {user.name}")

    guild = message.guild
    member = guild.get_member(user.id)
    role = guild.get_role(config.INCORRECT_ROLE_ID)

    await member.add_roles(role)

    try:
        await channel.send(f"Varul {user.mention} a cam ars-o si de data asta.")
        await channel.send(f"https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRwOh0fMbCuuqGMSzApkyleYJ-C9CYSJDMPQw&s")
        logger.debug(f"Sent message on channel regarding {user.name}'s role assignation.")
    except Exception as e :
        logger.error(f"Failed to send message on channel regarding {user.name}'s role assignation.")
    logger.debug(f"Finished assigning role to {user.name}.")


async def assign_roles_to_non_participants(message, users_answered):
    guild = message.guild
    role = guild.get_role(config.INCORRECT_ROLE_ID)

    if role is None:
        print(f"Error: Role with ID {config.INCORRECT_ROLE_ID} be found.")
        return #Stop further execution

    for member in guild.members:
        if member.id not in users_answered and not member.bot:
            await member.add_roles(role)