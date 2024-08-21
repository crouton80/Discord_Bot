import discord
from discord.ext import commands
import re
import random




intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.presences = True
bot = commands.Bot(command_prefix='?!', intents=intents)
bot_token = "MTI3NTE1ODIyODczMjIxOTQ5Nw.Gmspg-.Qo5Ran1hhLPS2KufkmNMd_MjgPP8X90afdNlJM"



@bot.event
async def on_ready():
    print(f'{bot.user} s-a conectat....aparent')

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.send(f'{member.mention} A intrat si el pe server. Ne pasa...')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    content_lower = message.content.lower()

    keywords = ['deah','mda','mhm','aha','dea']
    keywords_funny = ['amuzant', 'am intrebat', 'get laid']
    keywords_prietena = ['pizda', 'proasta', 'pzd', 'prst', 'femeie', 'woman', 'Paula', 'Adriana', 'Paoleu']
    sentences_teachings = [f'Lasa ai sa vezi tu cum e cand o sa ai prietena {message.author.mention}', f'Mai trebuie sa cresti {message.author.mention}', f'Aoleu ce ai cu femeile? {message.author.mention}']
    random_index = random.randint(0,2)
    random_sentence = sentences_teachings[random_index]
    
    #Exemplu de raspuns cu imagine la cuvant cheie
    if 'aoleu' in message.content.lower():
        await message.channel.send('https://media.discordapp.net/attachments/668446349309640704/1258854233348771950/caption-2.gif?ex=66c4e25d&is=66c390dd&hm=39fe2c5d0fbc3ad56d59d6943db68994406370aa1a623c0cde1a558cd1c09540&=&width=415&height=546')

    if any(word in content_lower for word in keywords_prietena):
        await message.channel.send(random_sentence)
    
    if any(re.search(rf'\b{word}\b', content_lower) for word in keywords):
        await message.channel.send('Dopamina celorlalti membri dupa citirea acestui mesaj: 📉')
    
    if any(re.search(rf'\b{word}\b', content_lower) for word in keywords_funny):
        role = discord.utils.get(message.guild.roles, name='Bro paid for nitro')

        if role in message.author.roles:
            await message.channel.send(f'How nigga {message.author.mention} with {role.mention} gets pussy?')
        else:
            pass
    
    if any(word in content_lower for word in ['ceseu', 'csgo', 'cs', 'skin']):
        await message.channel.send(f'{message.author.mention} Nu stii ma sa joci si tu jocuri adevarate gen Cyberpunk? alo')
    
@bot.event
async def on_presence_update(before, after):
    send_channel_id = 668446349309640704
    # check_channel_id = 1045795388344516722

    SERVER_ID = 660603940416651264

    # check_channel = bot.get_channel(check_channel_id)
    
    # Check if the activity changed
    if before.activity != after.activity:
        before_activity_name = before.activity.name if before.activity else None
        after_activity_name = after.activity.name if after.activity else None
        print(f"{after.name} has changed activity from {before_activity_name} to {after_activity_name}")

        # Make sure after.activity is not None and has the 'name' attribute
        if after.activity and hasattr(after.activity, 'name') and after_activity_name.lower() != "counter-strike 2":
            print(f"Varul {after.name} mai joaca si el alt ceva precum: {after.activity.name}")
            
        # Check if the new activity is an activity with that name
        if before_activity_name is None or before_activity_name.lower() != "counter-strike 2":
            print("Fara viata/nici o foaia stivata detected")

            guild = after.guild
            if guild and guild.id == SERVER_ID:
                send_channel = bot.get_channel(send_channel_id)
                await send_channel.send(f"{after.name}Vere te rog eu din suflet du-te si atinge iarba si lasa pacaneaua.")

            else:
                print(f"Bot is not in any guild.")
        else:
            print("No valid activity detected or 'name' attribute missing")
    else:
        print("No activity change detected")


def run_bot():  
    bot.run(bot_token)
    