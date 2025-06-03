from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Return a new ``AsyncEngine`` using ``database_url`` or ``DATABASE_URL`` env."""
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return create_async_engine(url, echo=False)


def get_sessionmaker(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Return an ``async_sessionmaker`` bound to ``engine`` or the default engine."""
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session(engine: AsyncEngine | None = None) -> AsyncIterator[AsyncSession]:
    """Yield an ``AsyncSession`` bound to ``engine`` in a context manager."""
    session_maker = get_sessionmaker(engine)
    async with session_maker() as session:
        yield session
