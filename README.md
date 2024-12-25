Here's a reformatted version of your README that enhances readability and adds structure for a more aesthetically pleasing and user-friendly experience:

---

# 🎶 Discord Music Bot with Voice Channel Automation

This project is a **customizable Discord bot** designed for **music playback** from YouTube and **voice channel management**. It offers features like **automated voice channel joining**, handling **age-restricted YouTube videos**, and customizable presence detection for users.

## 🚀 Features

### 🎶 **Music Playback**
- **Play music from YouTube** using URLs or search queries.
- Handles **age-restricted YouTube videos** with authentication (cookies or `.netrc` credentials).
  
**Commands for music control:**
- `?!play <url/search>`: Plays a song from YouTube or searches for a query.
- `?!pause`: Pauses the current playback.
- `?!resume`: Resumes paused playback.
- `?!stop`: Stops the playback.
- `?!leave`: Disconnects the bot from the voice channel.

### 🔊 **Voice Channel Management**
- Automatically joins a **specified voice channel** when a member enters.
- **Disconnects automatically** when the channel is empty.
  
**Commands to control auto-joining:**
- `?!stop_joining`: Stops the bot from auto-joining voice channels.
- `?!start_joining`: Enables auto-joining functionality.

### 🛠️ **Custom Presence Detection**
- Monitors **user presence updates** (e.g., playing a game).
- Sends notifications for specific activities, such as starting to play **Counter-Strike 2**.

### 📜 **Robust Error Handling**
- Gracefully handles edge cases such as:
  - Missing data
  - Network errors
  - Invalid commands
- Logs errors for debugging purposes.

## 📋 Commands Overview

| Command             | Description                                              |
|---------------------|----------------------------------------------------------|
| `?!play <url>`       | Plays a song from YouTube or searches for a query.       |
| `?!pause`            | Pauses the current playback.                             |
| `?!resume`           | Resumes paused playback.                                |
| `?!stop`             | Stops the playback.                                      |
| `?!leave`            | Disconnects the bot from the voice channel.              |
| `?!stop_joining`     | Disables auto-joining voice channels.                    |
| `?!start_joining`    | Enables auto-joining voice channels.                     |

## 📝 Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/discord-music-bot.git
   ```

2. **Install dependencies:**
   ```bash
   cd discord-music-bot
   pip install -r requirements.txt
   ```

3. **Set up your bot**: Follow the instructions in `config.json` to set up your bot token and other configuration settings.

4. **Run the bot:**
   ```bash
   python bot.py
   ```

---

### 💡 Customizing the Bot
You can modify the bot's behavior, including auto-joining voice channels and more, by adjusting settings in the `config.json` file.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

This formatting provides clear, structured sections with bolded headings and bullet points, making it easier to follow. You can also update the links and commands as per your project specifics.
