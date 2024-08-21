import discord
from discord.ext import commands
import re
import random
import yt_dlp
import asyncio

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.presences = True
intents.voice_states = True  # Enable voice state intent
bot = commands.Bot(command_prefix='?!', intents=intents)
bot_token = "MTI3NTE1ODIyODczMjIxOTQ5Nw.Gmspg-.Qo5Ran1hhLPS2KufkmNMd_MjgPP8X90afdNlJM"
# Set your specific voice channel ID and YouTube URL
VOICE_CHANNEL_ID = 805870131267895337
YOUTUBE_URL = "https://www.youtube.com/watch?v=49l39sSrGqk"


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
        if after_activity_name and after_activity_name.lower() == "counter-strike 2":

            if before_activity_name is None and before_activity_name.lower() != "counter-strike 2":
                print("Fara viata/nici o foaia stivata detected")

                guild = after.guild
                if guild and guild.id == SERVER_ID:
                    send_channel = bot.get_channel(send_channel_id)
                    await send_channel.send(f"{after.name} Vere te rog eu din suflet du-te si atinge iarba si lasa pacaneaua.")

                else:
                    print(f"Bot is not in any guild.")
            else:
                print("No valid activity detected or 'name' attribute missing")
    else:
        print("No activity change detected")


@bot.event
async def on_voice_state_update(member, before, after):
    voice_channel = bot.get_channel(VOICE_CHANNEL_ID)

    if voice_channel:
        print(f"Voice channel found: {voice_channel.name} (ID: {voice_channel.id})")
    else:
        print(f"Voice channel with ID {VOICE_CHANNEL_ID} not found.")
        return

    before_channel_id = before.channel.id if before.channel else None
    after_channel_id = after.channel.id if after.channel else None
    print(f"Member {member} - Before channel: {before_channel_id}, After channel: {after_channel_id}")

    if voice_channel.id in {before_channel_id, after_channel_id}:
        num_members = len(voice_channel.members)
        print(f"Members in {voice_channel.name}: {num_members}")

        voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
        
        # Handle connection based on member count
        if num_members > 1:
            if voice_client:
                if voice_client.channel.id != VOICE_CHANNEL_ID:
                    print(f"Bot is in a different channel. Disconnecting...")
                    await voice_client.disconnect()
                    print(f"Connecting to {voice_channel.name}")
                    await join_and_play(voice_channel)
                else:
                    print(f"Bot is already in the correct channel: {voice_channel.name}")
            else:
                print(f"Bot is not connected. Connecting to {voice_channel.name}")
                await join_and_play(voice_channel)
        else:
            if voice_client and voice_client.channel.id == VOICE_CHANNEL_ID:
                print(f"One or no members left in {voice_channel.name}. Bot should leave.")
                await voice_client.disconnect()

async def join_and_play(voice_channel):
    voice_client = None
    try:
        # Bot joins the channel
        if discord.utils.get(bot.voice_clients, guild=voice_channel.guild):
            print(f"Bot is already connected to a channel. Skipping connection.")
            return
        
        print(f"Attempting to connect to {voice_channel.name}")
        voice_client = await voice_channel.connect()
        print(f"Bot connected to {voice_channel.name}")

        # Set options for the worst quality audio stream
        ydl_opts = {
            'format': 'worstaudio/worst',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '48',
            }],
        }

        print(f"Fetching audio from {YOUTUBE_URL} with yt-dlp")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(YOUTUBE_URL, download=False)
            url2 = info['url']
            print(f"Extracted URL: {url2}")

        # Play the audio in the voice channel
        print(f"Playing audio from URL: {url2}")
        source = await discord.FFmpegOpusAudio.from_probe(url2)
        voice_client.play(source, after=lambda e: print('Finished playing!'))

        # Wait for the audio to finish playing
        while voice_client.is_playing():
            await asyncio.sleep(1)
        
        print(f"Audio playback completed.")
    except Exception as e:
        print(f"Error during join_and_play: {e}")
    finally:
        if voice_client:
            print(f"Disconnecting from {voice_channel.name}")
            await voice_client.disconnect()
            print(f"Bot disconnected from {voice_channel.name}")


def run_bot():  
    bot.run(bot_token)
    