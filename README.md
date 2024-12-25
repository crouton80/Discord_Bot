Discord Music Bot with Voice Channel Automation
This project is a powerful, customizable Discord bot designed for managing voice channels, playing music from YouTube, and handling user presence updates. The bot includes features like automated joining and leaving of voice channels, handling age-restricted YouTube videos, and commands for dynamic control over its behavior.

Features

🎶 Music Playback
Play music from YouTube using URLs or search queries.
Supports handling age-restricted videos with authentication through cookies or .netrc credentials.
Commands for managing playback:
?!play <url/search>: Play a song or search for it on YouTube.
?!pause: Pause the current playback.
?!resume: Resume paused playback.
?!stop: Stop the music.
?!leave: Disconnect the bot from the voice channel.

🔊 Voice Channel Management
Automatically joins a specified voice channel when a member enters.
Disconnects when the channel is empty.
Commands to enable or disable auto-joining:
?!stop_joining: Stops the bot from auto-joining voice channels.
?!start_joining: Restarts the auto-joining functionality.

🛠️ Custom Presence Detection
Monitors user presence updates.
Sends notifications for specific activities, e.g., starting to play "Counter-Strike 2."

📜 Robust Error Handling
Gracefully handles edge cases like missing data, network errors, or invalid commands.
Logs errors for debugging purposes.


Commands Overview
Command	Description
?!play <url>	Plays a song from YouTube or searches for a query.

?!pause	Pauses the current playback.

?!resume	Resumes paused playback.

?!stop	Stops the playback.

?!leave	Disconnects the bot from the voice channel.

?!stop_joining	Disables auto-joining voice channels.

?!start_joining	Enables auto-joining voice channels.

