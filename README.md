# 🎶 Multi-functional Discord BOT

This project is a customizable Discord bot designed to offer a wide range of functionalities. It supports **music playback** from YouTube, **voice channel management**, **trivia polling**, and even **dynamic meme fetching** using Selenium. The bot is built with modularity in mind, allowing you to easily extend its features and adjust its behavior through configuration files.

---

## 🚀 Features

### 🎶 Music Playback
- **Play music from YouTube** using either direct URLs or search queries.
- Handles **age-restricted YouTube videos** using cookies or `.netrc` authentication.
- Provides full music control with commands to pause, resume, stop playback, and disconnect from voice channels.
- Supports **m3u8 streaming** for YouTube live streams and HLS content.

**Commands:**
- `?!play <url/search>`: Plays a song from YouTube or searches for a query.
- `?!pause`: Pauses the current playback.
- `?!resume`: Resumes paused playback.
- `?!stop`: Stops the playback.
- `?!leave`: Disconnects the bot from the voice channel.

---

### 🔊 Voice Channel Management
- **Auto-join**: Automatically joins a specified voice channel when a member enters.
- **Auto-leave**: Disconnects automatically when the channel is empty.
- **Control Commands**: Enable or disable auto-joining behavior dynamically.

**Commands:**
- `?!stop_joining`: Disables the auto-joining functionality.
- `?!start_joining`: Re-enables auto-joining.

---

### ❓ Trivia Polling
- Fetches trivia questions and answers from a Trivia API.
- Posts daily polls in designated channels and processes responses.
- Assigns roles based on correct or incorrect answers, and even penalizes non-participants.
- **Toggle functionality**: Enable/disable polls dynamically without restarting the bot.

**Commands:**
- `?!toggle_polls`: Toggle daily trivia polls on/off.
- (Polls are automatically posted at scheduled intervals when enabled. See configuration in `poll_task.py`.)

---

### 🤖 Dynamic Meme Fetching
- Uses **Selenium** (or optionally cloudscraper) to simulate a web browser and fetch dynamic meme links from 9GAG.
- Scrapes JavaScript-rendered content that traditional HTTP requests may miss.
- Posts random 9GAG meme URLs and accompanying GIFs at regular intervals.
- **Toggle functionality**: Enable/disable meme posting dynamically without restarting the bot.

**Commands:**
- `?!toggle_9gag`: Toggle 9GAG meme posting on/off.
- (Meme posting runs automatically as a scheduled task when enabled. See `meme_task.py` for details.)

---

### 🔧 Configuration & Persistence
- **JSON-based settings**: Bot settings are stored in `settings.json` for persistence across restarts.
- **Runtime toggles**: All major features can be enabled/disabled at runtime without restarting.
- **Modular configuration**: Easy configuration through `config.py` and `settings.py`.

---

### 🔍 Custom Presence Detection
- Monitors user presence updates.
- Sends notifications when users start playing specified games (e.g., "Counter-Strike 2").
- Enhances engagement by dynamically reacting to users' activities.

---

## 📋 Commands Overview

| Command             | Description                                               |
|---------------------|-----------------------------------------------------------|
| `?!play <url/search>` | Plays a song from YouTube or searches for a query.        |
| `?!pause`          | Pauses the current playback.                              |
| `?!resume`         | Resumes paused playback.                                  |
| `?!stop`           | Stops the playback.                                       |
| `?!leave`          | Disconnects the bot from the voice channel.               |
| `?!stop_joining`   | Disables auto-joining voice channels.                     |
| `?!start_joining`  | Enables auto-joining functionality.                       |
| `?!toggle_polls`   | Toggle daily trivia polls on/off.                         |
| `?!toggle_9gag`    | Toggle 9GAG meme posting on/off.                          |

---

## 📝 Getting Started

### Prerequisites
- **Python 3.8+**: Download from [Python.org](https://www.python.org/).
- **FFmpeg**: Download and install from [FFmpeg.org](https://ffmpeg.org/). Ensure it is added to your system's PATH.
- **WebDriver (for Selenium)**:  
  - For example, [GeckoDriver for Firefox](https://github.com/mozilla/geckodriver) or [ChromeDriver for Chrome].  
- **Dependencies**: Install required packages using:
  ```bash
  pip install -r requirements.txt
### 🔧 Configuration (`config.py`)

You will need to set up your own `config.py` file with the following variables:

```python
# Discord bot authentication token
BOT_TOKEN = "<TOKEN>"

# Trivia API endpoint URL
TRIVIA_API_URL = "<TRIVIA_API>"

# List of text channel IDs for bot activity (e.g., trivia, polls)
CHANNEL_ID = [
    123456789012345678,
    987654321098765432
]

# Role ID assigned for incorrect trivia answers
INCORRECT_ROLE_ID = 123456789012345678

# Time limit (in seconds) for answering trivia questions
TIME_LIMIT_SECONDS = 30 * 60  # 30 minutes

# List of voice channel IDs for music playback and auto-join
VOICE_CHANNEL_ID = [
    234567890123456789,
    876543210987654321
]

# List of YouTube URLs for music playback
YOUTUBE_URLs = [
    "https://youtube.com/abc123",
    "https://youtube.com/def456",
    "https://youtube.com/ghi789"
]

# Enable/disable polls feature
POLLS_ENABLED = True

# Enable/disable 9GAG meme integration
NINEGAG_ENABLED = True

# Enable/disable polls feature
POLLS_ENABLED = True

# Enable/disable 9GAG meme integration
NINEGAG_ENABLED = True
