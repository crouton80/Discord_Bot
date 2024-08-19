import discord
from discord.ext import commands


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
    
    #Exemplu de raspuns cu imagine la cuvant cheie
    if 'aoleu' in message.content.lower():
        await message.channel.send('https://media.discordapp.net/attachments/668446349309640704/1258854233348771950/caption-2.gif?ex=66c4e25d&is=66c390dd&hm=39fe2c5d0fbc3ad56d59d6943db68994406370aa1a623c0cde1a558cd1c09540&=&width=415&height=546')
    
    if any(word in content_lower for word in ['deah','mda','mhm','aha','da','dea']):
        await message.channel.send('Dopamina celorlalti membri dupa citirea acestui mesaj: 📉')
    
    if any(word in content_lower for word in ['amuzant', 'Am intrebat', 'get laid']):
        role = discord.utils.get(message.guild.roles, name='Bro paid for nitro')

        if role in message.author.roles:
            await message.channel.send(f'Fratele {message.author.mention} a platit pentru nitro si nici nu stiveaza foaia.')
        else:
            pass
    
    if any(word in content_lower for word in ['ceseu', 'csgo', 'cs', 'skin']):
        await message.channel.send(f'{message.author.mention} Nu stii ma sa joci si tu jocuri adevarate precum Cyberpunk?')
    
@bot.event
async def on_presence_update(before, after):
    send_channel_id = 668446349309640704
    # check_channel_id = 1045795388344516722

    SERVER_ID = 660603940416651264

    # check_channel = bot.get_channel(check_channel_id)
    
    # Check if the activity changed
    if before.activity != after.activity:
        print(f"Activity changed from {before.activity} to {after.activity}")

        # Make sure after.activity is not None and has the 'name' attribute
        if after.activity and hasattr(after.activity, 'name'):
            print(f"Varul {after.name} mai joaca si el alt ceva precum: {after.activity.name}")
            
            # Check if the new activity is an activity with that name
            if after.activity.name.lower() == "counter-strike 2":
                print("Fara viata/nici o foaia stivata detected")

                guild = after.guild
                if guild and guild.id == SERVER_ID:
                    send_channel = bot.get_channel(send_channel_id)
                    await send_channel.send(f"{after.mention}Vere te rog eu din suflet du-te si atinge iarba si lasa pacaneaua.")

                else:
                    print(f"Bot is not in any guild.")
        else:
            print("No valid activity detected or 'name' attribute missing")
    else:
        print("No activity change detected")


def run_bot():  
    bot.run(bot_token)
    