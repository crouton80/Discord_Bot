"""Example configuration file.

Copy this file to config.py and fill in your values.
Never commit config.py to version control!
"""

# Discord bot authentication token
# You can also set this via DISCORD_BOT_TOKEN environment variable
BOT_TOKEN = "your_bot_token_here"

# Trivia API endpoint URL
# You can also set this via TRIVIA_API_URL environment variable
TRIVIA_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"

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

# List of YouTube URLs for music playback (used by auto-join feature)
YOUTUBE_URLs = [
    "https://www.youtube.com/watch?v=example1",
    "https://www.youtube.com/watch?v=example2",
    "https://www.youtube.com/watch?v=example3",
]

# Feature flags (these are now managed via settings.json)
# These are kept for backwards compatibility but are not used
POLLS_ENABLED = True
NINEGAG_ENABLED = True

