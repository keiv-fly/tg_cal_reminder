import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv

from tg_cal_reminder.bot import scheduler
from tg_cal_reminder.bot.polling import Poller
from tg_cal_reminder.bot.update import handle_update
from tg_cal_reminder.db.sessions import get_engine, get_sessionmaker
from tg_cal_reminder.llm.translator import translate_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    print("Starting bot...")
    load_dotenv()
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required")

    engine = get_engine()
    session_factory = get_sessionmaker(engine)

    async with (
        httpx.AsyncClient(base_url=f"https://api.telegram.org/bot{token}/") as tg_client,
        httpx.AsyncClient() as llm_client,
    ):

        async def translator(text: str, lang: str) -> dict:
            return await translate_message(llm_client, text, lang)

        poller = Poller(
            token,
            lambda u: handle_update(u, tg_client, session_factory, translator),
            client=tg_client,
        )
        sched = scheduler.create_scheduler()
        sched.start()
        try:
            print("Bot is now polling for updates...")
            await poller.run()
        finally:
            print("Shutting down bot...")
            sched.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
