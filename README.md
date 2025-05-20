# tg_cal_reminder

This is a telegram bot that will remind about different events in telegram.

I try to write the whole code with LLM tools like Codex, ChatGPT, and Cursor. 

Currently work in progress

## Database migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema
migrations. Ensure the ``DATABASE_URL`` environment variable is set before
running Alembic commands. Create the initial migration with:

```bash
alembic revision --autogenerate -m "initial"
```

Apply migrations using:

```bash
alembic upgrade head
```
