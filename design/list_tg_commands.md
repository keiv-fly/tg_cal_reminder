# List of telegram bot commands

(Anything in ⟨angle brackets⟩ is required; items in \[brackets] are optional.)

| Command                       | Parameters & Syntax                                                                               | What it does                                                                                                                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **/start**                    | –                                                                                                 | Begins the conversation and prompts the user for their preferred language.                                                                                                                |
| **/lang ⟨code⟩**              | **code** – two-letter ISO 639-1 language code (e.g., `en`, `fr`, `de`)                            | Changes the language the bot uses to reply.                                                                                                                                               |
| **/add\_event ⟨event\_line⟩** | **event\_line** – single line in the exact format<br/>`YYYY-MM-DD HH:MM [YYYY-MM-DD HH:MM] Title` | Saves a new calendar entry.<br/>• If the date/time is in the past, the bot saves it but warns the user.<br/>• If a second date/time is supplied, it is treated as the event’s *end* time. |
| **/list\_events \[username]** | **username** – Telegram @username or numeric ID of the target user (omit for yourself)            | Lists all events for the chosen user, sorted chronologically (open events first, then closed).                                                                                            |
| **/close\_event ⟨id …⟩**      | One or more **event ID** values, space-separated                                                  | Marks the specified events as *closed* (done/archived).                                                                                                                                   |
| **/help**                     | –                                                                                                 | Shows a short reminder of every command and its syntax.                                                                                                                                   |

---

### Automatic daily & weekly digests

These are *notifications*, not commands:

* **Every evening (local time):** list next day’s events.
* **Every morning:** list same-day events.
* **Every Monday morning:** list events for the coming week.

Users don’t need to request these; the bot sends them automatically based on the stored calendar data.
