import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from tg_cal_reminder.db import crud
from tg_cal_reminder.db.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    def session_factory() -> AsyncSession:
        return AsyncSession(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_get_user(async_session: AsyncSession):
    user = await crud.create_user(async_session, telegram_id=1, username="alice", language="en")
    assert user.id is not None
    fetched = await crud.get_user_by_telegram_id(async_session, 1)
    assert fetched == user


@pytest.mark.asyncio
async def test_get_user_not_found(async_session: AsyncSession):
    result = await crud.get_user_by_telegram_id(async_session, 999)
    assert result is None


@pytest.mark.asyncio
async def test_update_user_language(async_session: AsyncSession):
    user = await crud.create_user(async_session, telegram_id=2, username="bob")
    updated = await crud.update_user_language(async_session, user, "fr")
    assert updated.language == "fr"
    refreshed = await crud.get_user_by_telegram_id(async_session, user.telegram_id)
    assert refreshed.language == "fr"


@pytest.mark.asyncio
async def test_event_operations(async_session: AsyncSession):
    user = await crud.create_user(async_session, telegram_id=3, username="carol")
    now = datetime.datetime.now(datetime.UTC)

    e1 = await crud.create_event(async_session, user.id, now, title="e1")
    e2 = await crud.create_event(
        async_session,
        user.id,
        now + datetime.timedelta(hours=1),
        title="e2",
    )
    e3 = await crud.create_event(
        async_session,
        user.id,
        now + datetime.timedelta(hours=2),
        title="e3",
    )

    # close e2
    closed = await crud.close_events(async_session, user.id, [e2.id])
    assert closed == [e2.id]

    # ordering: open events first by start_time
    events_all = await crud.list_events(async_session, user.id)
    assert [e.id for e in events_all] == [e1.id, e3.id, e2.id]

    # filter out closed
    open_events = await crud.list_events(async_session, user.id, include_closed=False)
    assert {e.id for e in open_events} == {e1.id, e3.id}

    # get events between
    between = await crud.get_events_between(
        async_session,
        user.id,
        now,
        now + datetime.timedelta(hours=1, minutes=30),
    )
    assert [e.id for e in between] == [e1.id]

    ranged = await crud.list_events_between(
        async_session,
        user.id,
        now + datetime.timedelta(minutes=30),
        now + datetime.timedelta(hours=3),
    )
    assert [e.id for e in ranged] == [e3.id, e2.id]


@pytest.mark.asyncio
async def test_close_events_empty_and_cross_user(async_session: AsyncSession):
    user1 = await crud.create_user(async_session, telegram_id=10)
    user2 = await crud.create_user(async_session, telegram_id=20)
    now = datetime.datetime.now(datetime.UTC)

    await crud.create_event(async_session, user1.id, now, title="a")
    e2 = await crud.create_event(async_session, user2.id, now, title="b")

    # empty list
    assert await crud.close_events(async_session, user1.id, []) == []

    # attempt to close event owned by another user
    changed = await crud.close_events(async_session, user1.id, [e2.id])
    assert changed == []
    refreshed = await crud.list_events(async_session, user2.id)
    assert refreshed[0].is_closed is False

