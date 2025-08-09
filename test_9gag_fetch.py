from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
import time

def fetch_9gag_meme_selenium():
    # Set up the browser in headless mode
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    
    driver.get("https://9gag.com/fresh")
    time.sleep(3)  # Wait for JavaScript to load

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Extract meme links
    meme_links = []
    for a in soup.find_all("a", href=True):
        if "/gag/" in a['href']:
            full_url = "https://9gag.com" + a['href']
            meme_links.append(full_url)

    return meme_links

if __name__ == "__main__":
    links = fetch_9gag_meme_selenium()
    print(f"Found {len(links)} links.")
    for link in links:
        print(link)
