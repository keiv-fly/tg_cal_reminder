# CRUD operations for interacting with the database

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Event, User


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    language: str = "en",
    is_authorized: bool = False,
) -> User:
    """Create and return a new ``User`` record."""
    user = User(
        telegram_id=telegram_id,
        username=username,
        language=language,
        is_authorized=is_authorized,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Return ``User`` by Telegram ID or ``None`` if not found."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def update_user_language(session: AsyncSession, user: User, language: str) -> User:
    """Update a user's language preference."""
    user.language = language
    await session.commit()
    await session.refresh(user)
    return user


async def authorize_user(session: AsyncSession, user: User) -> User:
    """Mark ``user`` as authorized."""
    user.is_authorized = True
    await session.commit()
    await session.refresh(user)
    return user


async def create_event(
    session: AsyncSession,
    user_id: int,
    start_time: datetime,
    title: str,
    end_time: datetime | None = None,
) -> Event:
    """Create an event for ``user_id`` and return it."""
    event = Event(user_id=user_id, start_time=start_time, end_time=end_time, title=title)
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def list_events(
    session: AsyncSession,
    user_id: int,
    include_closed: bool = True,
) -> list[Event]:
    """Return events for a user ordered with open events first."""
    stmt = select(Event).where(Event.user_id == user_id)
    if not include_closed:
        stmt = stmt.where(Event.is_closed.is_(False))
    stmt = stmt.order_by(Event.is_closed, Event.start_time)
    result = await session.execute(stmt)
    return list(result.scalars())


async def close_events(
    session: AsyncSession,
    user_id: int,
    event_ids: Sequence[int],
) -> list[int]:
    """Mark the specified events as closed. Returns list of IDs that changed."""
    if not event_ids:
        return []

    stmt = (
        update(Event)
        .where(and_(Event.user_id == user_id, Event.id.in_(event_ids), Event.is_closed.is_(False)))
        .values(is_closed=True)
        .returning(Event.id)
    )
    result = await session.execute(stmt)
    await session.commit()
    return [row[0] for row in result.fetchall()]


async def get_events_between(
    session: AsyncSession,
    user_id: int,
    start: datetime,
    end: datetime,
) -> list[Event]:
    """Return open events for ``user_id`` between ``start`` and ``end`` inclusive."""
    stmt = (
        select(Event)
        .where(
            Event.user_id == user_id,
            Event.start_time >= start,
            Event.start_time <= end,
            Event.is_closed.is_(False),
        )
        .order_by(Event.start_time)
    )
    result = await session.execute(stmt)
    return list(result.scalars())
