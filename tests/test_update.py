import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tg_cal_reminder.bot.update import handle_update
from tg_cal_reminder.db import crud
from tg_cal_reminder.db.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_handle_update_creates_user_and_sends_message(monkeypatch, session_factory):
    history: list[tuple[httpx.URL, bytes]] = []

    async def transport_handler(request: httpx.Request) -> httpx.Response:
        history.append((request.url, request.content))
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(transport_handler)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://api.telegram.org/botTOKEN/"
    ) as tg_client:

        async def dummy_dispatch(session, user, text, lang, translator):
            return "ok"

        monkeypatch.setattr("tg_cal_reminder.bot.handlers.dispatch", dummy_dispatch)

        update = {
            "message": {"text": "/start", "chat": {"id": 1}, "from": {"id": 5, "username": "bob"}}
        }
        await handle_update(update, tg_client, session_factory, lambda *_: None)

    assert history
    url, content = history[0]
    assert url.path.endswith("/sendMessage")
    assert b"chat_id=1" in content
    assert b"text=ok" in content

    async with session_factory() as session:
        user = await crud.get_user_by_telegram_id(session, 5)
        assert user is not None


@pytest.mark.asyncio
async def test_handle_update_ignores_invalid_update(session_factory):
    called = []

    async def transport_handler(request: httpx.Request) -> httpx.Response:
        called.append(request)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(transport_handler)
    async with httpx.AsyncClient(transport=transport) as tg_client:
        await handle_update({}, tg_client, session_factory, lambda *_: None)

    assert not called
    async with session_factory() as session:
        result = await crud.get_user_by_telegram_id(session, 5)
        assert result is None
