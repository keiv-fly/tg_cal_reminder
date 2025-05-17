# Original prompt start
You are an experienced requirements writer. Create requirements for the following program: 

# Original

The program is a telegram bot that connects to telegram using httpx library and http telegram bot api. The program will have a postgresql database. The program will be able to connect to openrouter llm models and have the following features:
1. Save events to calendar for a telegram user 
2. Show all events sorted by time for a user talking with the bot and also for an arbitrary user
3. Close events based on its ids.
4. Every evening show the events planned for the next day
5. Every morning show the events planned for the same day
6. On Monday show the events for the week.

All the commands should be fixed commands that do not need LLM to work. But there should be llm to be able to understand arbotrary commands that could be converted to fix commands. 

# Change 1
Change the language of the answer to the preferred language of the user. Remove compliance. Past data events are allowed but with a warning that it is in the past. The format to save the message should start with a date and time and then the title should follow without semicolon as a separator.

# Change 2
The requirements should be in English. The bot should ask the preferred language at the start. 

# Change 3
The end date should follow after the beginning date and still be optional.

# Change 4
There should be no webhooks. The bot will poll telegram messages.
