import asyncio
import logging
import os

import httpx
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

from tg_cal_reminder.bot import scheduler
from tg_cal_reminder.bot.commands import register_commands
from tg_cal_reminder.bot.polling import Poller
from tg_cal_reminder.bot.update import handle_update
from tg_cal_reminder.db.sessions import get_engine, get_sessionmaker
from tg_cal_reminder.llm.translator import translate_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting bot...")
    load_dotenv()
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required")

    engine = get_engine()
    session_factory = get_sessionmaker(engine)

    # Run migrations to ensure the database schema is up to date.
    # Alembic's upgrade command uses ``asyncio.run`` internally which would
    # block the running event loop, so run it in a separate thread instead.
    await asyncio.to_thread(command.upgrade, Config("alembic.ini"), "head")
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    root_level = getattr(logging, level_name, logging.INFO)
    logging.getLogger().setLevel(root_level)

    async with (
        httpx.AsyncClient(base_url=f"https://api.telegram.org/bot{token}/") as tg_client,
        httpx.AsyncClient() as llm_client,
    ):

        async def translator(text: str, lang: str, tz: str) -> dict:
            return await translate_message(llm_client, text, lang, tz)

        await register_commands(tg_client)

        poller = Poller(
            token,
            lambda u: handle_update(u, tg_client, session_factory, translator),
            client=tg_client,
        )
        sched = scheduler.create_scheduler()
        sched.start()
        try:
            logger.info("Bot is now polling for updates...")
            await poller.run()
        finally:
            logger.info("Shutting down bot...")
            sched.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
