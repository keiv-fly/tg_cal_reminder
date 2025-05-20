
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from tg_cal_reminder.db import sessions
from tg_cal_reminder.db.models import Base, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def test_get_engine_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    engine = sessions.get_engine()
    try:
        assert isinstance(engine, AsyncEngine)
        assert str(engine.url) == TEST_DATABASE_URL
    finally:
        # Ensure disposal even if assertions fail
        import asyncio
        asyncio.run(engine.dispose())


def test_get_engine_custom_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    engine = sessions.get_engine(TEST_DATABASE_URL)
    try:
        assert str(engine.url) == TEST_DATABASE_URL
    finally:
        import asyncio
        asyncio.run(engine.dispose())


def test_get_engine_missing_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        sessions.get_engine()


@pytest_asyncio.fixture
async def engine():
    engine = sessions.get_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_session_context(engine):
    async with sessions.get_session(engine) as session:
        user = User(telegram_id=1)
        session.add(user)
        await session.commit()

    async with sessions.get_session(engine) as session:
        result = await session.execute(select(User))
        assert result.scalar_one().telegram_id == 1
