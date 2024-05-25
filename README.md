# Project Setup

This document provides instructions on how to setup and run this bot application.

## Prerequisites

Ensure you have Python installed. This project was built using version 3.11.4.

Install the following external libraries using pip:

- apscheduler: `pip install apscheduler`
- colorama: `pip install colorama`
- PIL: `pip install pillow`

## Setup

1. **Download this GitHub project** to your server/machine.

2. **Install the required external libraries**:

    - apscheduler: Used for asynchronous scheduling, similar to cron jobs, for firing event triggers.
    - colorama: Used for colored text output for the console.
    - PIL: Used to combine randomly selected boss images.

3. **Rename 'config EXAMPLE.json'** to 'config.json' in the same location (the root of the program). The program only looks for 'config.json' and will fail if this file is not present.

4. **Create a bot** on the [Discord Developer Portal](https://discord.com/developers/applications). The bot must have the following intents enabled:
    - Presence intent
    - Server members intent
    - Message content intent

5. **Enable Developer Mode** on your Discord server. Go to 'User Settings' > 'App Settings' > 'Appearance' > 'Advanced', and toggle on 'Developer Mode'.

6. **Configure the bot** in the 'config.json' file. All of these values are mandatory for the bot to work:

    - `discord["bot token"]`: <string> The TOKEN for your Discord bot.
    - `discord["voting channel id"]`: <int> The channel ID for voting.
    - `discord["leaderboard channel id"]`: <int> The channel ID for the leaderboard display.
    - `discord["set name channel id"]`: <int> The channel ID for users to set their OSRS name association.
    - `discord["console channel id"]`: <int> The channel ID for ADMINS to use bot commands.
    - `discord["admin list"]`: <string array> A list of Discord usernames allowed to run bot commands.

    - `event["vote open day"]`: <string> The day when voting opens (e.g., "monday", "tuesday", etc.).
    - `event["vote open time"]`: <string> The time when voting opens, in "00:00" format.

    - `api["url"]`: <string> The WiseOldMan API URL.
    - `api["discord contact name"]`: <string> Your Discord name for WiseOldMan API usage terms.
    - `api["bulk update frequency"]`: <int> The frequency (in minutes) for bulk updates from the WiseOldMan API.