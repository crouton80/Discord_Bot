import discord
import config

reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

def construct_poll_message(question, all_answers):
    poll_message = f"**Ia sa vedem mai ai neuroni?**\n\n{question}\n"
    for i, answer in enumerate(all_answers):
        poll_message += f"{i+1}. {answer}\n"
    return poll_message

async def add_reactions(poll_message, all_asnwers):
    for i in range(len(all_asnwers)):
        await poll_message.add_reaction(reactions[i])

async def process_poll_results(message, all_answers, correct_answer, bot):
    #Track users who answered and their answers
    users_answered = set()
    for reaction in message.reactions:
        if reaction.emoji in reactions:
            async for user in reactions.users():
                if user != bot.user and user.id not in users_answered:
                    selected_answer = reactions.index(reaction.emoji)
                    users_answered.add(user.id)

                    member = message.guild.get_member(user.id)
                    incorrect_role = message.guild.get_role(config.INCORRECT_ROLE_ID)

                    # If user chose correct answer, remove his incorrect role
                    if all_answers[selected_answer] == correct_answer:
                        if incorrect_role in member.roles:
                            await member.remove_roles(incorrect_role)
                            await message.channel.send(f"{user.mention} Hai vere ca ai trecut cu 5-ul de doamne ajuta. Ai 5 clase acuma.")
                        else:
                            await message.channel.send(f"{user.mention} ai vazut, ce usor a fost? ehe")

                    else:
                        await assign_incorrect_role(message, user)
                        await message.channel.send(f"{user.mention} https://www.dgaspc-sectorul1.ro/despre-noi/directia-persoana-si-familie/centrul-de-abilitare-si-reabilitare-pentru-persoane-adulte-cu-dizabilitati-milcov/")

    
    # Assign incorrect roles to non-participants
    await assign_roles_to_non_participants(message, users_answered)

async def assign_incorrect_role(message, user):
    guild = message.guild
    member = guild.get_member(user.id)
    role = guild.get_role(config.INCORRECT_ROLE_ID)
    await member.add_roles(role)
    await message.channel.send(f"Varul {user.mention} a cam ars-o si de data asta.")

async def assign_roles_to_non_participants(message, users_answered):
    guild = message.guild
    for member in guild.members:
        if member.id not in users_answered and not member.bot:
            role = guild.get_role(config.INCORRECT_ROLE_ID)
            await member.add_roles(role)