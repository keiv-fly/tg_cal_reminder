# File Structure

calendar_bot/
├── .env                        # Environment variables: BOT_TOKEN, DATABASE_URL, OPENROUTER_API_KEY
├── README.md                   # Project overview, installation, usage instructions
├── pyproject.toml              # Python project metadata and dependencies
├── alembic.ini                 # Configuration for Alembic database migrations
├── migrations/                 # Alembic-generated migration scripts
│   └── versions/
│       └── xxxx_initial.py     # Initial schema setup: users and events tables
├── src/                        # Application source code
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