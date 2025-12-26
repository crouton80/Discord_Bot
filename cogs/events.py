"""Event handlers for the Discord bot."""
import discord
from discord.ext import commands
import re
import random
import logging

logger = logging.getLogger(__name__)


class EventsCog(commands.Cog):
    """Handles Discord events like messages, member joins, and presence updates."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Message response keywords
        self.keywords = ['deah', 'mda', 'mhm', 'aha', 'dea', 'real', 'lol']
        self.keywords_funny = ['amuzant', 'am intrebat', 'get laid', 'ne pasa', 'mata']
        self.keywords_prietena = ['pizda', 'proasta', 'pzd', 'prst', 'femeie', 'woman', 'Paula', 'Adriana', 'Paoleu']
        self.sentences_teachings = [
            f'Lasa ai sa vezi tu cum e cand o sa ai prietena {{mention}}',
            f'Mai trebuie sa cresti {{mention}}',
            f'Aoleu ce ai cu femeile? {{mention}}'
        ]
        
        # Presence monitoring
        self.send_channel_ids = [668446349309640704, 1139931838660476949]
        self.server_ids = [660603940416651264, 1139931837381234708]
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'{self.bot.user} has connected to Discord')
        
        # Start background tasks if enabled (only if not already running)
        from poll_task import start_daily_poll
        from meme_task import start_meme_poster
        
        # These functions now check if tasks are already running
        start_daily_poll(self.bot)
        start_meme_poster(self.bot)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins the server."""
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'{member.mention} A intrat si el pe server. Ne pasa...')
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called when a message is sent."""
        if message.author == self.bot.user:
            return

        # Note: discord.py's default handler already calls `process_commands`.
        # Calling it here (in a cog listener) can cause commands to run twice.

        content_lower = message.content.lower()
        
        # Special response for 'aoleu'
        if 'aoleu' in content_lower:
            await message.channel.send(
                'https://media.discordapp.net/attachments/668446349309640704/1258854233348771950/caption-2.gif?ex=66c4e25d&is=66c390dd&hm=39fe2c5d0fbc3ad56d59d6943db68994406370aa1a623c0cde1a558cd1c09540&=&width=415&height=546'
            )
        
        # Check for keywords_prietena
        if any(word in content_lower for word in self.keywords_prietena):
            random_sentence = random.choice(self.sentences_teachings).format(mention=message.author.mention)
            await message.channel.send(random_sentence)
        
        # Check for keywords
        if any(re.search(rf'\b{word}\b', content_lower) for word in self.keywords):
            await message.channel.send('Dopamina celorlalti membri dupa citirea acestui mesaj: 📉')
        
        # Check for keywords_funny
        if any(re.search(rf'\b{word}\b', content_lower) for word in self.keywords_funny):
            role = discord.utils.get(message.guild.roles, name='Bro paid for nitro')
            if role in message.author.roles:
                await message.channel.send(
                    f'How nigga {message.author.mention} with {role.mention} gets pussy?'
                )
        
        # Gaming-related responses
        if any(word in content_lower for word in ['ceseu', 'csgo', 'cs', 'skin', 'gaming']):
            await message.channel.send(
                f'{message.author.mention} Nu stii ma sa joci si tu jocuri adevarate gen Cyberpunk? alo'
            )
    
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Called when a member's presence is updated."""
        # Check if the activity changed
        if before.activity != after.activity:
            before_activity_name = before.activity.name if before.activity else None
            after_activity_name = after.activity.name if after.activity else None
            logger.debug(f"{after.name} changed activity from {before_activity_name} to {after_activity_name}")
            
            # Make sure after.activity is not None and has the 'name' attribute
            if after.activity and hasattr(after.activity, 'name') and after_activity_name.lower() != "counter-strike 2":
                logger.debug(f"Varul {after.name} mai joaca si el alt ceva precum: {after.activity.name}")
                for channel_id in self.send_channel_ids:
                    send_channel = discord.utils.get(after.guild.text_channels, id=channel_id)
                    if send_channel:
                        logger.debug(f"Varul {after.name} mai face si el alt ceva precum: {after.activity.name}")
                        # await send_channel.send(f"Varul {after.name} mai face si el alt ceva precum: {after.activity.name}")
            
            elif after_activity_name and after_activity_name.lower() == "counter-strike 2":
                if not before_activity_name or before_activity_name.lower() != after_activity_name.lower():
                    guild = after.guild
                    if guild and guild.id in self.server_ids:
                        for channel_id in self.send_channel_ids:
                            send_channel = discord.utils.get(guild.text_channels, id=channel_id)
                            if send_channel:
                                await send_channel.send(
                                    f"{after.name} Vere te rog eu din suflet du-te si atinge iarba si lasa pacaneaua."
                                )


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(EventsCog(bot))

