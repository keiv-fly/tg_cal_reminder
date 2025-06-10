# List of telegram bot commands

(Anything in ⟨angle brackets⟩ is required; items in [brackets] are optional.)

| Command                       | Parameters & Syntax                                              | What it does                                                                 |
| ----------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **/start**                    | –                                                                | Begins the conversation and prompts the user for their preferred language. |
| **/lang ⟨code⟩**              | **code** – two-letter ISO 639-1 language code (e.g., `en`, `fr`) | Changes the language the bot uses to reply.                                 |
| **/add_event ⟨event_line⟩**   | **event_line** – `YYYY-MM-DD HH:MM [YYYY-MM-DD HH:MM] Title`     | Saves a new calendar entry. Past dates are allowed but trigger a warning.   |
| **/edit_event ⟨id⟩ ⟨event_line⟩** | **id** – event ID<br>**event_line** – same format as above | Updates an existing event with new details.                                  |
| **/list_events [username]**   | **username** – Telegram @username or numeric ID                 | Lists all events for the chosen user, open events first.                     |
| **/list_all_events [from to]**| Optional start and end date/time                                | Lists events in the specified range.                                        |
| **/close_event ⟨id …⟩**       | One or more **event ID** values                                  | Marks the specified events as *closed*.                                      |
| **/help**                     | –                                                                | Shows a short reminder of every command and its syntax.                      |

---

### Automatic daily & weekly digests

These are *notifications*, not commands:

* **Every evening (local time):** list next day’s events.
* **Every morning:** list same-day events.
* **Every Monday morning:** list events for the coming week.

Users don’t need to request these; the bot sends them automatically based on the stored calendar data.
