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
    events = await crud.list_events(async_session, user.id)
    assert len(events) == 1
    ev = events[0]
    expected_time = now.astimezone(datetime.UTC).strftime("%Y-%m-%d %H:%M")
    assert (
        result
        == f"Event {ev.id} added: {expected_time} {ev.title} | id={ev.id}"
    )



@pytest.mark.asyncio
async def test_dispatch_free_text_uses_translator(async_session: AsyncSession, user: User):
    translator = AsyncMock(return_value={"command": "/help", "args": []})

    result = await handlers.dispatch(async_session, user, "what can you do?", "en", translator)

    translator.assert_called_once()
    assert result.startswith("/start") or result.startswith("/lang") or "help" in result


@pytest.mark.asyncio
async def test_handle_timezone(async_session: AsyncSession, user: User) -> None:
    ctx = handlers.CommandContext(async_session, user)
    reply = await handlers.handle_timezone(ctx, "Europe/Berlin")
    assert "Timezone updated" in reply
    refreshed = await crud.get_user_by_telegram_id(async_session, user.telegram_id)
    assert refreshed.timezone == "Europe/Berlin"


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

    list_text_after_close = await handlers.handle_list_events(
        handlers.CommandContext(async_session, user), ""
    )
    assert f"id={event1.id}" not in list_text_after_close
    assert f"id={event2.id}" in list_text_after_close

    result = await async_session.execute(select(User))
    assert result.scalar_one()

    events = await crud.list_events(async_session, user.id)
    closed_ids = [e.id for e in events if e.is_closed]
    assert event1.id in closed_ids
    assert event2.id not in closed_ids


@pytest.mark.asyncio
async def test_handle_list_events_no_events(async_session: AsyncSession, user: User) -> None:
    text = await handlers.handle_list_events(handlers.CommandContext(async_session, user), "")
    assert text == "No events found"


@pytest.mark.asyncio
async def test_handle_list_all_events(async_session: AsyncSession, user: User):
    now = datetime.datetime.now(datetime.UTC)
    event1 = await crud.create_event(async_session, user.id, now, "A")
    event2 = await crud.create_event(
        async_session, user.id, now + datetime.timedelta(hours=2), "B"
    )

    ctx = handlers.CommandContext(async_session, user)
    all_text = await handlers.handle_list_all_events(ctx, "")
    assert str(event1.id) in all_text and str(event2.id) in all_text

    start = (now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    end = (now + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
    filtered = await handlers.handle_list_all_events(ctx, f"{start} {end}")
    filtered_ids = {line.split()[0] for line in filtered.splitlines()}
    assert str(event1.id) not in filtered_ids and str(event2.id) in filtered_ids


@pytest.mark.asyncio
async def test_handle_edit_event(async_session: AsyncSession, user: User) -> None:
    now = datetime.datetime.now(datetime.UTC)
    event = await crud.create_event(async_session, user.id, now, "Old")
    new_time = (now + datetime.timedelta(hours=1)).replace(second=0, microsecond=0)
    ctx = handlers.CommandContext(async_session, user)
    args = f"{event.id} {new_time.strftime('%Y-%m-%d %H:%M')} New"
    result = await handlers.handle_edit_event(ctx, args)
    assert "updated" in result
    refreshed = (await crud.list_events(async_session, user.id))[0]
    assert refreshed.title == "New" and refreshed.start_time == new_time


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
    assert reply == "Please provide a secret"

    # wrong secret
    reply = await handlers.dispatch(async_session, user, "wrong", "en")
    assert reply == "The secret is wrong. Please provide a secret"

    # correct secret authorizes user
    reply = await handlers.dispatch(async_session, user, "topsecret", "en")
    assert reply == 'Please write your preferred language using command "/lang en"'

    refreshed = await crud.get_user_by_telegram_id(async_session, 99)
    assert refreshed is not None and refreshed.is_authorized is True


@pytest.mark.asyncio
async def test_handle_list_events_grouping(
    async_session: AsyncSession, user: User, monkeypatch
) -> None:
    now = datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.UTC)

    class FixedDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz: datetime.tzinfo | None = None) -> "FixedDateTime":
            return cls.fromtimestamp(now.timestamp(), tz or now.tzinfo)

    monkeypatch.setattr(handlers, "datetime", FixedDateTime)

    e1 = await crud.create_event(
        async_session,
        user.id,
        now + datetime.timedelta(hours=1),
        "First",
    )
    e2 = await crud.create_event(
        async_session,
        user.id,
        now + datetime.timedelta(days=1, hours=2),
        "Second",
    )
    e3 = await crud.create_event(
        async_session,
        user.id,
        now + datetime.timedelta(days=5, hours=3),
        "Third",
    )
    e4 = await crud.create_event(
        async_session,
        user.id,
        now + datetime.timedelta(days=7, hours=4),
        "Fourth",
    )

    ctx = handlers.CommandContext(async_session, user)
    text = await handlers.handle_list_events(ctx, "")

    assert "Today:" in text
    assert "Tomorrow:" in text
    assert "Fri:" in text
    assert "2025-06-08:" in text
    for ev in (e1, e2, e3, e4):
        assert f"id={ev.id}" in text


@pytest.mark.asyncio
async def _prepare_start(async_session: AsyncSession, user: User):
    async def check(result: str) -> None:
        assert result == "Please provide a secret"
    return "/start", "", check


@pytest.mark.asyncio
async def _prepare_lang(async_session: AsyncSession, user: User):
    async def check(result: str) -> None:
        assert result == "Language updated to ru"
        refreshed = await crud.get_user_by_telegram_id(async_session, user.telegram_id)
        assert refreshed.language == "ru"
    return "/lang", "ru", check


@pytest.mark.asyncio
async def _prepare_add_event(async_session: AsyncSession, user: User):
    now = (
        datetime.datetime.now(datetime.UTC).replace(second=0, microsecond=0)
        + datetime.timedelta(days=1)
    )
    event_line = f"{now.strftime('%Y-%m-%d %H:%M')} Test"

    async def check(result: str) -> None:
        events = await crud.list_events(async_session, user.id)
        assert len(events) == 1
        ev = events[0]
        expected_time = now.astimezone(datetime.UTC).strftime('%Y-%m-%d %H:%M')
        assert result == f"Event {ev.id} added: {expected_time} {ev.title} | id={ev.id}"
    return "/add_event", event_line, check


@pytest.mark.asyncio
async def _prepare_edit_event(async_session: AsyncSession, user: User):
    now = datetime.datetime.now(datetime.UTC).replace(second=0, microsecond=0)
    ev = await crud.create_event(async_session, user.id, now, "Old")
    new_time = now + datetime.timedelta(hours=1)
    args = f"{ev.id} {new_time.strftime('%Y-%m-%d %H:%M')} New"

    async def check(result: str) -> None:
        assert "updated" in result
        refreshed = (await crud.list_events(async_session, user.id))[0]
        assert refreshed.title == "New"
        assert refreshed.start_time.replace(tzinfo=datetime.UTC) == new_time
    return "/edit_event", args, check


@pytest.mark.asyncio
async def _prepare_list_events(async_session: AsyncSession, user: User):
    now = datetime.datetime.now(datetime.UTC)
    later = now + datetime.timedelta(hours=1)
    ev1 = await crud.create_event(async_session, user.id, now, "First")
    ev2 = await crud.create_event(async_session, user.id, later, "Second")

    async def check(result: str) -> None:
        assert f"id={ev1.id}" in result and f"id={ev2.id}" in result
    return "/list_events", "", check


@pytest.mark.asyncio
async def _prepare_list_all_events(async_session: AsyncSession, user: User):
    now = datetime.datetime.now(datetime.UTC)
    ev1 = await crud.create_event(async_session, user.id, now, "A")
    ev2 = await crud.create_event(async_session, user.id, now + datetime.timedelta(hours=1), "B")

    async def check(result: str) -> None:
        assert str(ev1.id) in result and str(ev2.id) in result
    return "/list_all_events", "", check


@pytest.mark.asyncio
async def _prepare_timezone(async_session: AsyncSession, user: User):
    async def check(result: str) -> None:
        assert result == "Timezone updated to Europe/Berlin"
        refreshed = await crud.get_user_by_telegram_id(async_session, user.telegram_id)
        assert refreshed.timezone == "Europe/Berlin"
    return "/timezone", "Europe/Berlin", check


@pytest.mark.asyncio
async def _prepare_close_event(async_session: AsyncSession, user: User):
    now = datetime.datetime.now(datetime.UTC)
    ev = await crud.create_event(async_session, user.id, now, "ToClose")

    async def check(result: str) -> None:
        assert str(ev.id) in result and "Closed" in result
        refreshed = (await crud.list_events(async_session, user.id))[0]
        assert refreshed.is_closed
    return "/close_event", str(ev.id), check


@pytest.mark.asyncio
async def _prepare_help(async_session: AsyncSession, user: User):
    async def check(result: str) -> None:
        assert "/add_event" in result and "/help" in result
    return "/help", "", check


_PREPARERS = [
    _prepare_start,
    _prepare_lang,
    _prepare_add_event,
    _prepare_edit_event,
    _prepare_list_events,
    _prepare_list_all_events,
    _prepare_timezone,
    _prepare_close_event,
    _prepare_help,
]


@pytest.mark.asyncio
@pytest.mark.parametrize("preparer", _PREPARERS)
async def test_dispatch_translator_error_none(async_session: AsyncSession, user: User, preparer):
    command, args, checker = await preparer(async_session, user)
    translator = AsyncMock(return_value={"command": command, "args": args, "error": None})

    result = await handlers.dispatch(async_session, user, "text", "en", translator)

    translator.assert_called_once()
    await checker(result)
