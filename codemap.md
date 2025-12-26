# Code Map

High-level guide to the structure and runtime flow of this Discord bot.

All file references are written as Markdown links (e.g. [bot.py#L72](bot.py#L72)) so you can Ctrl+Click to jump in most IDEs.

## Top-level entry points

- Main entry: [main.py#L13](main.py#L13)
  - Imports `run_bot`: [main.py#L11](main.py#L11)
- Bot bootstrap/runtime: [bot.py#L1](bot.py#L1)
  - Bot instance: [bot.py#L25](bot.py#L25)
  - Extension loader: [bot.py#L31](bot.py#L31)
  - Setup: [bot.py#L57](bot.py#L57)
  - Run: [bot.py#L72](bot.py#L72)

## Runtime flow (mental model)

1. Process starts: [main.py#L13](main.py#L13)
2. Bot setup + connect: `run_bot()` at [bot.py#L72](bot.py#L72)
   - `Config.load_from_file("config.py")`: [bot.py#L60](bot.py#L60) -> [utils/config.py#L92](utils/config.py#L92)
   - `Config.validate()`: [bot.py#L63](bot.py#L63) -> [utils/config.py#L143](utils/config.py#L143)
   - Load cogs: `load_extensions()` at [bot.py#L31](bot.py#L31)
3. When connected:
   - Bot-level ready log: [bot.py#L49](bot.py#L49)
   - Cog ready handler starts background tasks: [cogs/events.py#L32](cogs/events.py#L32)

## Configuration & settings

### Central configuration (`utils/config.py`)

- `Config` class: [utils/config.py#L25](utils/config.py#L25)
- Defaults for `settings.json`: [utils/config.py#L19](utils/config.py#L19)
- Settings persistence:
  - Load: [utils/config.py#L54](utils/config.py#L54)
  - Save: [utils/config.py#L72](utils/config.py#L72)
  - Get/Set: [utils/config.py#L79](utils/config.py#L79), [utils/config.py#L85](utils/config.py#L85)
- Legacy `config.py` loader: [utils/config.py#L92](utils/config.py#L92)
- FFmpeg discovery: [utils/config.py#L122](utils/config.py#L122)
- Validation (requires token): [utils/config.py#L143](utils/config.py#L143)

### Persisted toggles

- Feature flags file: [settings.json#L1](settings.json#L1)

### Local secrets / IDs

- Example template: [config.example.py#L1](config.example.py#L1)
- Local config (do not commit): [config.py#L1](config.py#L1) (ignored via [.gitignore#L139](.gitignore#L139))

## Logging

- Logging setup: [utils/logger.py#L5](utils/logger.py#L5)
- Used by bot bootstrap: [bot.py#L15](bot.py#L15)

## Cogs (Discord extensions)

Loaded from `bot.py:load_extensions()` at [bot.py#L31](bot.py#L31).

### Events / listeners (`cogs/events.py`)

- Cog: [cogs/events.py#L11](cogs/events.py#L11)
- Starts background tasks: [cogs/events.py#L32](cogs/events.py#L32)
- Message handler (also calls `process_commands`): [cogs/events.py#L52](cogs/events.py#L52)
- Presence monitor: [cogs/events.py#L92](cogs/events.py#L92)
- Extension entrypoint: [cogs/events.py#L121](cogs/events.py#L121)

### Admin toggles (`cogs/admin.py`)

- Cog: [cogs/admin.py#L12](cogs/admin.py#L12)
- `?!toggle_polls`: [cogs/admin.py#L19](cogs/admin.py#L19)
  - Starts/stops task: [poll_task.py#L14](poll_task.py#L14)
  - Persists toggle: [utils/config.py#L85](utils/config.py#L85)
- `?!toggle_9gag`: [cogs/admin.py#L38](cogs/admin.py#L38)
  - Starts/stops task: [meme_task.py#L223](meme_task.py#L223)
  - Persists toggle: [utils/config.py#L85](utils/config.py#L85)
- Extension entrypoint: [cogs/admin.py#L57](cogs/admin.py#L57)

### Auto voice join/play (`cogs/autovoice.py`)

- Cog: [cogs/autovoice.py#L13](cogs/autovoice.py#L13)
- Listener: [cogs/autovoice.py#L22](cogs/autovoice.py#L22)
- Uses FFmpeg discovery: [cogs/autovoice.py#L19](cogs/autovoice.py#L19) -> [utils/config.py#L122](utils/config.py#L122)
- Extension entrypoint: [cogs/autovoice.py#L240](cogs/autovoice.py#L240)

### YouTube playback (`cogs/youtube.py`)

- Cog: [cogs/youtube.py#L28](cogs/youtube.py#L28)
- Voice connect helper: [cogs/youtube.py#L38](cogs/youtube.py#L38)
- Core playback: [cogs/youtube.py#L157](cogs/youtube.py#L157)
- Main command: `?!play` decorator: [cogs/youtube.py#L405](cogs/youtube.py#L405)
- Seek commands:
  - `?!seek`: [cogs/youtube.py#L475](cogs/youtube.py#L475)
  - `?!forward`: [cogs/youtube.py#L504](cogs/youtube.py#L504)
  - `?!back`: [cogs/youtube.py#L519](cogs/youtube.py#L519)
- Extension entrypoint: [cogs/youtube.py#L535](cogs/youtube.py#L535)

## Background tasks

### Trivia polls (`poll_task.py`)

- Loop decorator: [poll_task.py#L13](poll_task.py#L13)
- Loop function: [poll_task.py#L14](poll_task.py#L14)
- Start gate (checks `polls_enabled`): [poll_task.py#L69](poll_task.py#L69) -> [utils/config.py#L79](utils/config.py#L79)

Supporting modules:

- Trivia fetch: [trivia_api.py#L6](trivia_api.py#L6)
- Poll + roles logic:
  - Build message: [roles_management.py#L11](roles_management.py#L11)
  - Add reactions: [roles_management.py#L17](roles_management.py#L17)
  - Process results: [roles_management.py#L21](roles_management.py#L21)

### 9GAG memes (`meme_task.py`)

- Tracker class: [meme_task.py#L35](meme_task.py#L35) (writes [sent_memes.json#L1](sent_memes.json#L1))
- Scrape/select meme: [meme_task.py#L128](meme_task.py#L128)
- Loop decorator: [meme_task.py#L222](meme_task.py#L222)
- Loop function: [meme_task.py#L223](meme_task.py#L223)
- Start gate (checks `9gag_enabled`): [meme_task.py#L235](meme_task.py#L235) -> [utils/config.py#L79](utils/config.py#L79)

## Other / legacy / dev scripts

- Older settings helper: [settings.py#L1](settings.py#L1)
- Older YouTube implementation (not loaded as a cog): [youtube.py#L1](youtube.py#L1)
- Local/dev scripts: [test.py#L1](test.py#L1), [test_permissions.py#L1](test_permissions.py#L1), [test_9gag_fetch.py#L1](test_9gag_fetch.py#L1)

## Dependencies

- Python deps list: [requirements.txt#L1](requirements.txt#L1)

## Where to add things

- New commands/features: add a cog under [cogs/](cogs/) and register it in [bot.py#L31](bot.py#L31).
- New background loop: start it from [cogs/events.py#L32](cogs/events.py#L32) and optionally add a toggle in [cogs/admin.py#L12](cogs/admin.py#L12).
- New persisted toggle: add to defaults in [utils/config.py#L19](utils/config.py#L19) and use [utils/config.py#L79](utils/config.py#L79) / [utils/config.py#L85](utils/config.py#L85).

