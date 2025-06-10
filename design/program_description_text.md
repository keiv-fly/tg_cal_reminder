# Original prompt start
You are an experienced requirements writer. Create requirements for the following program: 

# Program Description
Telegram bot using **httpx** with the Telegram HTTP Bot API, a **PostgreSQL** database, and **OpenRouter LLM** support.

* There should be a secret word that will allow the user to use the bot. This secret is given after /start.
* On first contact after sending secret word the bot asks the user’s preferred language, then answers in that language.
* All requirements are written in English.
* Commands are fixed
* the LLM only translates free-form user text into those commands
* Event format: `YYYY-MM-DD HH:MM [optional YYYY-MM-DD HH:MM] Title` (no semicolon). Past dates are accepted but trigger a warning.

## Features
1. Save events to a user’s calendar.
2. Show all events, sorted by time, for the current or any specified user.
3. Edit existing events by ID.
4. Close events by their IDs.
5. Every evening, list events planned for the next day.
6. Every morning, list events planned for the same day.
7. Every Monday, list events planned for the week.

The bot polls Telegram for messages—no webhooks are used.


