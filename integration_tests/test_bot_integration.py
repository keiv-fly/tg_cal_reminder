import httpx
import pytest
import respx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import os

from tg_cal_reminder.bot.polling import Poller
from tg_cal_reminder.bot.update import handle_update
from tg_cal_reminder.db import crud
from tg_cal_reminder.db.models import Base, User

from dotenv import load_dotenv

load_dotenv()

UPDATE = {
    "ok": True,
    "result": [
        {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 1234, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 1234, "type": "private"},
                "text": "/start",
            },
        }
    ],
}


@pytest.fixture(scope="session")
def integration_enabled():
    if not os.environ.get("RUN_INTEGRATION_TESTS"):
        pytest.skip("integration tests disabled", allow_module_level=True)


@pytest.fixture(scope="session")
def db_url(integration_enabled) -> str:
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def session_factory(db_url):
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def telegram_mock(integration_enabled):
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://api.telegram.org/botTEST_TOKEN/getUpdates").respond(
            json=UPDATE, status_code=200
        )
        mock.post("https://api.telegram.org/botTEST_TOKEN/sendMessage").respond(
            json={"ok": True, "result": {}}, status_code=200
        )
        yield mock


@pytest.mark.asyncio
async def test_start_command_creates_user(session_factory, telegram_mock):

    async with httpx.AsyncClient(base_url="https://api.telegram.org/botTEST_TOKEN/") as tg_client:
        poller = Poller(
            "TEST_TOKEN",
            lambda u: handle_update(u, tg_client, session_factory, lambda *_: None),
            client=tg_client,
        )
        await poller.poll_once()

    async with session_factory() as session:
        user: User | None = await crud.get_user_by_telegram_id(session, 1234)
        assert user is not None
        assert user.telegram_id == 1234

    send_calls = [c for c in telegram_mock.calls if c.request.method == "POST"]
    assert any("/sendMessage" in c.request.url.path for c in send_calls)
