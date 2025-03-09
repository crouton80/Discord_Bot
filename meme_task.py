import random
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from discord.ext import tasks
import config
import logging

logger = logging.getLogger(__name__)

def fetch_9gag_meme():
    try:
        url = "https://9gag.com/fresh"
        
        # Set up Firefox in headless mode
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        
        # Initialize Firefox WebDriver using webdriver_manager
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        
        driver.get(url)
        # Wait a few seconds for JavaScript to load the dynamic content
        time.sleep(6)
        
        # Parse the rendered page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        meme_links = []
        for a in soup.find_all("a", href=True):
            href = a['href']
            # Adjust this condition if necessary (here we check if "/gag/" is in the href)
            if "/gag/" in href:
                full_url = f"https://9gag.com{href}"
                meme_links.append(full_url)

        if meme_links:
            return random.choice(meme_links)
        return None 
    
    except Exception as e:
        logger.error(f"Failed to fetch 9GAG: {e}")
        return None

@tasks.loop(minutes=10)
async def post_meme(bot):
    meme_url = fetch_9gag_meme()
    if meme_url:
        for channel_id in config.CHANNEL_ID:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(meme_url)
                await channel.send("https://media.tenor.com/G5Xz2KGKMqkAAAAi/wojak-pointing.gif")
                logger.debug(f"Posted meme in channel {channel.name}")
    else:
        logger.error("No meme found to send.")

def start_meme_poster(bot):
    post_meme.start(bot)
