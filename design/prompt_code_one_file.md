Given this program description, file structure, list of tg commands and specification create a code for file db/models.py

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
3. Close events by their IDs.
4. Every evening, list events planned for the next day.
5. Every morning, list events planned for the same day.
6. Every Monday, list events planned for the week.

The bot polls Telegram for messages—no webhooks are used.

# File Structure

calendar_bot/
├── .env                        # Environment variables: BOT_TOKEN, DATABASE_URL, OPENROUTER_API_KEY
├── README.md                   # Project overview, installation, usage instructions
├── pyproject.toml              # Python project metadata and dependencies
├── alembic.ini                 # Configuration for Alembic database migrations
├── migrations/                 # Alembic-generated migration scripts
│   └── versions/
│       └── xxxx_initial.py     # Initial schema setup: users and events tables
├── tg_cal_reminder/            # Application source code
│   ├── bot/                    # Bot logic and scheduling
│   │   ├── __init__.py         
│   │   ├── polling.py          # HTTP polling loop using httpx to fetch Telegram updates
│   │   ├── handlers.py         # Dispatches incoming messages to command handlers via LLM translation
│   │   └── scheduler.py        # Defines scheduled tasks for daily, evening, and weekly digests
│   ├── db/                     # Database layer
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy ORM models: User and Event definitions
│   │   ├── crud.py             # CRUD functions: add_event, list_events, close_event, etc.
│   │   └── session.py          # Async engine and session factory (asyncpg/SQLAlchemy)
│   ├── i18n/                   # Internationalization
│   │   ├── __init__.py
│   │   └── messages.py         # Localized message templates keyed by lang_code
│   ├── llm/                    # LLM integration
│   │   ├── __init__.py
│   │   └── translator.py       # OpenRouter prompt construction and command translation logic
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py
│   │   ├── parser.py           # Parses event strings (YYYY-MM-DD HH:MM ...) and validates dates
│   │   └── timezones.py        # Europe/Paris timezone helpers and date calculations
│   └── main.py                 # Entrypoint: loads config, initializes DB, starts polling & scheduler
└── tests/                      # Test suite
    ├── unit/                  # Unit tests for individual modules
    │   ├── test_polling.py     # Tests for polling.py logic
    │   ├── test_handlers.py    # Tests for command handling in handlers.py
    │   ├── test_scheduler.py   # Tests for scheduled tasks definitions
    │   ├── test_models.py      # Tests for ORM models in models.py
    │   ├── test_crud.py        # Tests for CRUD functions in crud.py
    │   ├── test_session.py     # Tests for DB session in session.py
    │   ├── test_messages.py    # Tests for localized messages in messages.py
    │   ├── test_translator.py  # Tests for translator logic in translator.py
    │   ├── test_parser.py      # Tests for event parsing in parser.py
    │   └── test_timezones.py   # Tests for timezone helpers in timezones.py
    └── integration/           # End-to-end integration tests
        └── test_end_to_end.py  # Simulates bot flow: user registration, add/list/close events

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


# Specification

Below is a consolidated specification that pulls together everything in the description, file-tree and command table, plus the implicit constraints that follow from them.
Use it as the single source-of-truth when implementing, testing and reviewing the project.

---

## 1. High-level purpose

A Telegram bot that lets each authorised user maintain a personal calendar, receive automatic digests, and interact in **any supported language** while the implementation language remains **English**.
The bot:

* talks to Telegram **strictly via long-polling using httpx** (no web-hooks)
* persists data in **PostgreSQL** (async SQLAlchemy + asyncpg)
* off-loads free-form user input to **OpenRouter LLM** which returns one of the **fixed commands**
* runs on Europe/Paris time for scheduling digests.

---

## 2. Functional requirements

| #         | Requirement                                                                                                                                                                                                                                                                                  |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FR-1**  | **Secret access gate**: after `/start`, the bot sends a one-time secret word. Messages are ignored until the sender replies with that exact word.                                                                                                                                            |
| **FR-2**  | **Language onboarding**: as soon as the secret is accepted, ask for user’s preferred language (`/lang <code>` behind the scenes) and store it. Replies must thereafter be localised via `i18n/messages.py`.                                                                                  |
| **FR-3**  | **Rigid command set**: only the commands in § 3 are accepted. All free-text is routed through the LLM translator which must emit one of those commands or an error.                                                                                                                          |
| **FR-4**  | **/add\_event**: accept exactly `YYYY-MM-DD HH:MM [YYYY-MM-DD HH:MM] Title` (no semicolons).<br/>• If end-time is omitted the event is open-ended.<br/>• If start < now(), save anyway but warn the user.<br/>• Both datetimes are stored in UTC; display is converted to the user’s locale. |
| **FR-5**  | **/list\_events \[username]**: list events for the target (default = caller) in chronological order: (1) open events, (2) closed events, each with ID, start, end (if any) and title.                                                                                                        |
| **FR-6**  | **/close\_event \<id …>**: mark one or many events as closed; ignore unknown IDs; report which ones changed.                                                                                                                                                                                 |
| **FR-7**  | **/lang <code>** at any time updates the language and persists it.                                                                                                                                                                                                                           |
| **FR-8**  | **/help** prints a concise multilingual cheat-sheet of every command and the event format.                                                                                                                                                                                                   |
| **FR-9**  | **Automatic digests** (sent only to the owner of the events):<br/>• every evening (19:00) – events for the next day<br/>• every morning (08:00) – events for today<br/>• every Monday 08:00 – events for Mon-Sun of the current week                                                         |
| **FR-10** | **Past-date warning rule**: any event whose start is in the past triggers a warning message at creation time but remains valid.                                                                                                                                                              |
| **FR-11** | **Idempotent polling**: updates processed once must never be re-processed. Store last Telegram update\_id and resume from there after restart.                                                                                                                                               |
| **FR-12** | **Admin-less**: all functionality is per-user; there is no global admin role.                                                                                                                                                                                                                |

---

## 3. User-visible commands (strict grammar)

```
/start
/lang <code>                 # ISO-639-1, two letters
/add_event <event_line>      # rigid syntax above
/list_events [username]
/close_event <id …>
/help
```

---

## 4. Non-functional requirements

### 4.1 Architecture & tech stack

* Python 3.12+, **httpx** for Telegram polling & sending.
* **asyncio** everywhere; do not mix sync DB calls with async I/O.
* **OpenRouter** LLM accessed by HTTPS; retries & exponential back-off on failures.
* **SQLAlchemy 2.x** ORM, async engine, PostgreSQL 14+.
* **Alembic** migrations (versioned in *migrations/*).
* **apscheduler** or equivalent for in-process cron-like jobs (`scheduler.py`).

### 4.2 Internationalisation

* `i18n/messages.py` exposes a flat dict `MESSAGES = {lang_code: {key: str}}`.
* Missing translation falls back to **English**.
* All user-facing text passes through this layer (including warnings, errors, digests).

### 4.3 Error handling & resilience

* Network/LLM/database errors are logged and surfaced to the user in their language as a generic failure message; commands must never crash the polling loop.
* Invalid command or malformed parameters → localised usage help without stack-traces.
* Parsing errors in `/add_event` pinpoint which token failed (date / time / title).

### 4.4 Security & configuration

* Secrets supplied only via environment variables in `.env` (never committed):
  `BOT_TOKEN`, `DATABASE_URL`, `OPENROUTER_API_KEY`, `SECRET_WORD`.
* Use **parameterised queries** (ORM) – no string SQL.
* TLS enforced on all outbound HTTP connections.

### 4.5 Performance

* Polling interval adaptive: 1 s when updates are incoming, up to 5 s idle.
* DB indices: `Event(start_time)`, `Event(is_closed)`, `User(telegram_id UNIQUE)`.

### 4.6 Testing

* **100 % path coverage** on parsing, CRUD, translation logic, scheduler time windows.
* End-to-end test spins up a test Postgres (Docker) and mocks Telegram/LLM.

---

## 5. Data model (ORM)

| Table      | Field        | Type             | Notes                             |
| ---------- | ------------ | ---------------- | --------------------------------- |
| **users**  | id           | PK               | serial                            |
|            | telegram\_id | bigint UNIQUE    | numeric chat/user id              |
|            | username     | text             | Telegram `@username` if available |
|            | language     | char(2)          | ISO-639-1                         |
|            | created\_at  | timestamptz      | default = now()                   |
| **events** | id           | PK               | serial                            |
|            | user\_id     | FK → users.id    | cascade delete                    |
|            | start\_time  | timestamptz      | not null                          |
|            | end\_time    | timestamptz NULL | optional                          |
|            | title        | text             |                                   |
|            | is\_closed   | bool             | default false                     |
|            | created\_at  | timestamptz      | default = now()                   |

---

## 6. Scheduling logic

*All times Europe/Paris.*

| Job            | Cron‐like schedule | Query filter                                                                                   | Recipients         |
| -------------- | ------------------ | ---------------------------------------------------------------------------------------------- | ------------------ |
| Morning digest | `0 8 * * *`        | events where `date(start_time)=today` AND `is_closed=false`                                    | each event’s owner |
| Evening digest | `0 19 * * *`       | events where `date(start_time)=tomorrow` AND `is_closed=false`                                 | owner              |
| Weekly digest  | `0 8 * * 1`        | events where `start_time` in \[Mon 00:00, Sun 23:59] of current ISO week AND `is_closed=false` | owner              |

---

## 7. LLM translator contract

* Input: raw message text (`text`, `language_code` from Telegram).
* Output JSON: `{ "command": "/add_event", "args": "2025-05-20 14:00 Dentist" }` **or** `{ "error": "Unrecognized" }`.
* Must be prompt-engineered so that the LLM **never invents new commands** and always replies in English (the bot will translate to the user’s language afterwards).

---

## 8. File-structure invariants

* Nothing outside *src/* imports from *tests/* or vice-versa.
* **Circular-import–free**: `bot.handlers` may import `db.crud` but not the reverse.
* `utils.parser` and `llm.translator` contain **no Telegram-specific code** (pure helpers).

---

## 9. Deployment & operations

1. `docker compose up –d` starts Postgres; alembic migrations auto-run on start-up.
2. The bot process is a single service; horizontal scaling would require external job queue and distributed lock for the scheduler – **out of scope**.
3. Logging: human-readable INFO logs to stdout; DEBUG enabled via `LOG_LEVEL=DEBUG`.

---

## 10. Out-of-scope / explicit non-features

* No web UI or REST API.
* No multi-tenant shared calendars; each event belongs to exactly one Telegram user.
* No file attachments or rich media—text-only.
* No password resets or account deletion (Telegram’s own identity is sufficient).

---

### Completion criteria

The project is “done” when:

* All tests in *tests/*\*\* pass (`pytest -q` shows green).
* Manual check with a real Telegram bot token demonstrates the full happy-path:
  secret → language → add/list/close event → morning/evening/weekly digests.
* Code style: **ruff** (PEP 8) passes with no errors.

---

This document captures every known functional, technical and organisational requirement derived from the original brief and should be kept alongside the codebase (e.g. as *REQUIREMENTS.md*) to guide implementation and review.
