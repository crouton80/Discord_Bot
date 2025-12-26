import random
import time
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from discord.ext import tasks
from utils.config import Config
import logging
import threading

logger = logging.getLogger(__name__)

# Silence very verbose Selenium/urllib3 debug logs (page source, HTTP traces)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.WARNING)

# Persistent storage for sent meme IDs
SENT_MEMES_FILE = "sent_memes.json"
MAX_STORED_MEMES = 1000  # Keep track of up to 1000 sent memes
MEME_COOLDOWN_HOURS = 24  # Don't repeat memes for 24 hours

# Lock for thread-safe file operations (must be defined before MemeTracker)
_file_lock = threading.Lock()

class MemeTracker:
    def __init__(self):
        self.sent_memes = self._load_sent_memes()
    
    def _load_sent_memes(self):
        """Load previously sent meme IDs from file (thread-safe)"""
        with _file_lock:
            try:
                if os.path.exists(SENT_MEMES_FILE):
                    with open(SENT_MEMES_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Convert timestamp strings back to datetime objects
                        return {meme_id: datetime.fromisoformat(timestamp) 
                               for meme_id, timestamp in data.items()}
                return {}
            except Exception as e:
                logger.warning(f"Failed to load sent memes: {e}")
                return {}
    
    def _save_sent_memes(self):
        """Save sent meme IDs to file (thread-safe)"""
        with _file_lock:
            try:
                # Convert datetime objects to ISO format strings for JSON serialization
                data = {meme_id: timestamp.isoformat() 
                       for meme_id, timestamp in self.sent_memes.items()}
                
                # Use atomic write to prevent file corruption
                temp_file = f"{SENT_MEMES_FILE}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Atomic rename (works on Windows too)
                if os.path.exists(SENT_MEMES_FILE):
                    os.replace(temp_file, SENT_MEMES_FILE)
                else:
                    os.rename(temp_file, SENT_MEMES_FILE)
            except Exception as e:
                logger.error(f"Failed to save sent memes: {e}")
                # Clean up temp file if it exists
                temp_file = f"{SENT_MEMES_FILE}.tmp"
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
    
    def is_meme_recent(self, meme_id):
        """Check if a meme was sent recently (within cooldown period)"""
        if meme_id not in self.sent_memes:
            return False
        
        sent_time = self.sent_memes[meme_id]
        cooldown_end = sent_time + timedelta(hours=MEME_COOLDOWN_HOURS)
        return datetime.now() < cooldown_end
    
    def mark_meme_sent(self, meme_id):
        """Mark a meme as sent"""
        self.sent_memes[meme_id] = datetime.now()
        
        # Clean up old entries to prevent file from growing too large
        if len(self.sent_memes) > MAX_STORED_MEMES:
            # Remove oldest entries
            sorted_memes = sorted(self.sent_memes.items(), key=lambda x: x[1])
            entries_to_remove = len(self.sent_memes) - MAX_STORED_MEMES
            for meme_id_to_remove, _ in sorted_memes[:entries_to_remove]:
                del self.sent_memes[meme_id_to_remove]
        
        self._save_sent_memes()
    
    def cleanup_old_memes(self):
        """Remove memes older than cooldown period"""
        cutoff_time = datetime.now() - timedelta(hours=MEME_COOLDOWN_HOURS)
        old_memes = [meme_id for meme_id, timestamp in self.sent_memes.items() 
                    if timestamp < cutoff_time]
        
        for meme_id in old_memes:
            del self.sent_memes[meme_id]
        
        if old_memes:
            self._save_sent_memes()
            logger.debug(f"Cleaned up {len(old_memes)} old meme entries")

# Global meme tracker instance
meme_tracker = MemeTracker()

def _create_firefox_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    # options.page_load_strategy = 'eager'  # Optional: faster loads
    service = FirefoxService(GeckoDriverManager().install())
    return webdriver.Firefox(service=service, options=options)

def fetch_9gag_meme():
    try:
        # Clean up old memes periodically
        meme_tracker.cleanup_old_memes()
        
        sections = [
            "https://9gag.com/trending",
            "https://9gag.com/fresh",
            "https://9gag.com/hot",
        ]

        last_exception = None
        for attempt in range(3):
            # Try multiple sections per attempt
            for url in sections:
                driver = None
                try:
                    driver = _create_firefox_driver()
                    driver.get(url)
                    # Wait up to 15s for gag links to appear
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/gag/"]'))
                    )

                    # Parse the rendered page source with BeautifulSoup
                    soup = BeautifulSoup(driver.page_source, "html.parser")

                    # Collect unique gag IDs from links to avoid duplicates on the same page
                    gag_ids = set()
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if "/gag/" not in href:
                            continue
                        parsed = urlparse(href)
                        path = parsed.path or ""
                        if "/gag/" not in path:
                            # Handles fully-qualified URLs where '/gag/' is in query, etc.
                            continue
                        try:
                            gag_id = path.split("/gag/")[1].split("/")[0]
                        except Exception:
                            continue
                        if gag_id:
                            gag_ids.add(gag_id)

                    # Build full URLs and filter out recently sent ones
                    all_candidates = [f"https://9gag.com/gag/{gid}" for gid in gag_ids]
                    if not all_candidates:
                        continue

                    # Filter out recently sent memes
                    fresh_candidates = []
                    for url in all_candidates:
                        meme_id = url.rsplit("/", 1)[-1]
                        if not meme_tracker.is_meme_recent(meme_id):
                            fresh_candidates.append(url)

                    # If we have fresh candidates, choose from them
                    if fresh_candidates:
                        chosen = random.choice(fresh_candidates)
                        chosen_id = chosen.rsplit("/", 1)[-1]
                        meme_tracker.mark_meme_sent(chosen_id)
                        logger.debug(f"Selected fresh meme: {chosen_id}")
                        return chosen
                    
                    # If no fresh candidates, log this and try next section
                    logger.debug(f"No fresh memes found in {url}, trying next section")

                    # No acceptable candidate in this section; try next section
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt+1}/3 section fetch failed ({url}): {e}")
                finally:
                    if driver is not None:
                        try:
                            driver.quit()
                        except Exception:
                            pass

            # Backoff before next attempt across all sections
            time.sleep(1 + attempt)

        if last_exception:
            raise last_exception
        
        # If we get here, all sections were exhausted without finding fresh memes
        logger.warning("No fresh memes found in any section - all memes are within cooldown period")
        return None 
    
    except Exception as e:
        logger.error(f"Failed to fetch 9GAG: {e}")
        return None


@tasks.loop(minutes=10)
async def post_meme(bot):
    meme_url = fetch_9gag_meme()
    if meme_url:
        for channel_id in Config.CHANNEL_IDS:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(meme_url)
                await channel.send("https://media.tenor.com/G5Xz2KGKMqkAAAAi/wojak-pointing.gif")
                logger.debug(f"Posted meme in channel {channel.name}")
    else:
        logger.warning("No fresh meme found to send (all memes are within cooldown period)")

def start_meme_poster(bot):
    if Config.get_setting("9gag_enabled"):
        if not post_meme.is_running():
            logger.info("Starting 9GAG meme poster task")
            post_meme.start(bot)
        else:
            logger.debug("9GAG meme poster task is already running")
