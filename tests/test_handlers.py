import datetime
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from tg_cal_reminder.bot import handlers
from tg_cal_reminder.db import crud
from tg_cal_reminder.db.models import Base, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    def async_session_factory() -> AsyncSession:
        return AsyncSession(engine, expire_on_commit=False)

    async with async_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def user(async_session: AsyncSession) -> User:
    return await crud.create_user(
        async_session, telegram_id=1, username="tester", is_authorized=True
    )


@pytest.mark.asyncio
async def test_dispatch_direct_add_event(async_session: AsyncSession, user: User):
    translator = AsyncMock()
    now = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    text = f"/add_event {now.strftime('%Y-%m-%d %H:%M')} Test"

    result = await handlers.dispatch(async_session, user, text, "en", translator)

    assert translator.call_count == 0
    assert result.startswith("Event ")

    events = await crud.list_events(async_session, user.id)
    assert len(events) == 1
    assert events[0].title == "Test"


@pytest.mark.asyncio
async def test_dispatch_free_text_uses_translator(async_session: AsyncSession, user: User):
    translator = AsyncMock(return_value={"command": "/help", "args": ""})

    result = await handlers.dispatch(async_session, user, "what can you do?", "en", translator)

    translator.assert_called_once()
    assert result.startswith("/start") or result.startswith("/lang") or "help" in result


@pytest.mark.asyncio
async def test_handle_list_and_close(async_session: AsyncSession, user: User):
    now = datetime.datetime.now(datetime.UTC)
    event1 = await crud.create_event(async_session, user.id, now, "First")
    event2 = await crud.create_event(
        async_session, user.id, now + datetime.timedelta(hours=1), "Second"
    )

    list_text = await handlers.handle_list_events(handlers.CommandContext(async_session, user), "")
    assert str(event1.id) in list_text and str(event2.id) in list_text

    close_result = await handlers.handle_close_event(
        handlers.CommandContext(async_session, user), str(event1.id)
    )
    assert "Closed" in close_result

    result = await async_session.execute(select(User))
    assert result.scalar_one()

    events = await crud.list_events(async_session, user.id)
    closed_ids = [e.id for e in events if e.is_closed]
    assert event1.id in closed_ids
    assert event2.id not in closed_ids


@pytest.mark.asyncio
async def test_parse_event_line_errors():
    with pytest.raises(handlers.HandlerError):
        await handlers.parse_event_line("invalid event")


@pytest.mark.asyncio
async def test_secret_flow(async_session: AsyncSession, monkeypatch):
    monkeypatch.setenv("BOT_SECRET", "topsecret")
    user = await crud.create_user(async_session, telegram_id=99, is_authorized=False)

    assert not user.is_authorized

    # /start prompts for secret
    reply = await handlers.dispatch(async_session, user, "/start", "en")
    assert reply == "Please provide secret"

    # wrong secret
    reply = await handlers.dispatch(async_session, user, "wrong", "en")
    assert reply == "Please provide a secret"

    # correct secret authorizes user
    reply = await handlers.dispatch(async_session, user, "topsecret", "en")
    assert reply == 'Please write your preferred language using command "/lang en"'

    refreshed = await crud.get_user_by_telegram_id(async_session, 99)
    assert refreshed is not None and refreshed.is_authorized is True
