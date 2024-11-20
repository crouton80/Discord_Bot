import os
import logging
import yt_dlp
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('youtube_downloader')

class YouTubeDownloader:
    def __init__(self, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None, 
                 cookies_path: Optional[str] = None):
        self.username = username
        self.password = password
        self.cookies_path = cookies_path

    def _get_ydl_opts(self, download: bool = False) -> Dict[str, Any]:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'no_color': True,
            'verbose': True,
            'default_search': 'ytsearch1',
            'logger': logger,
        }

        # Priority-based authentication
        if self.cookies_path and os.path.exists(self.cookies_path):
            logger.info(f"Using cookies from file: {self.cookies_path}")
            ydl_opts['cookiefile'] = self.cookies_path
        else:
            # Try browser cookies
            ydl_opts['cookiesfrombrowser'] = ('chrome', None, None, None)

        return ydl_opts

    def extract_info(self, url: str) -> Dict[str, Any]:
        try:
            with yt_dlp.YoutubeDL(self._get_ydl_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    info = info['entries'][0]
                
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('url'),
                    'duration': info.get('duration'),
                    'view_count': info.get('view_count'),
                    'uploader': info.get('uploader')
                }
        except Exception as e:
            logger.error(f"Error extracting video info: {e}")
            raise

def main():
    # Test different authentication methods
    downloaders = [
        # Method 1: Cookies file
        YouTubeDownloader(cookies_path=r'C:\Users\Lorgar\Downloads\cookies.txt'),
        
        # Method 2: Browser cookies
        YouTubeDownloader()  # Will use browser cookies by default
    ]

    test_urls = [
        "tarantula cantec",  # Search query
        "https://www.youtube.com/watch?v=J269qszwiVI"  # Specific video URL
    ]

    for downloader in downloaders:
        print("\n--- Testing Downloader Configuration ---")
        for url in test_urls:
            try:
                print(f"\nTesting URL: {url}")
                video_info = downloader.extract_info(url)
                
                print("Video Info:")
                for key, value in video_info.items():
                    print(f"{key.capitalize()}: {value}")
            
            except Exception as e:
                print(f"Error processing {url}: {e}")

if __name__ == "__main__":
    main()