import datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from tg_cal_reminder.db.models import Base, Event, User

# Test database URL - use SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    """Create a test database and session fixture"""
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


@pytest.mark.asyncio
async def test_user_model_creation(async_session):
    """Test User model creation with default values"""
    # Create a test user
    user = User(telegram_id=123456789, username="testuser", language="en")

    # Add to session and commit
    async_session.add(user)
    await async_session.commit()

    # Query to verify - ADD EAGER LOADING HERE
    from sqlalchemy.orm import selectinload

    result = await async_session.execute(
        select(User).options(selectinload(User.events)).where(User.telegram_id == 123456789)
    )
    queried_user = result.scalar_one()

    # Assertions
    assert queried_user.id is not None
    assert queried_user.telegram_id == 123456789
    assert queried_user.username == "testuser"
    assert queried_user.language == "en"
    assert isinstance(queried_user.created_at, datetime.datetime)
    assert queried_user.events == []


@pytest.mark.asyncio
async def test_user_unique_constraint(async_session):
    """Test that telegram_id must be unique"""
    # Create two users with the same telegram_id
    user1 = User(telegram_id=123456789, username="user1", language="en")
    user2 = User(telegram_id=123456789, username="user2", language="fr")

    # Add first user
    async_session.add(user1)
    await async_session.commit()

    # Try to add second user with same telegram_id - should fail
    async_session.add(user2)
    with pytest.raises(IntegrityError):
        await async_session.commit()

    # Rollback for next tests
    await async_session.rollback()


@pytest.mark.asyncio
async def test_user_default_language(async_session):
    """Test that the default language is 'en'"""
    # Create user without specifying language
    user = User(telegram_id=123456790)

    # Add to session and commit
    async_session.add(user)
    await async_session.commit()

    # Query to verify
    result = await async_session.execute(select(User).where(User.telegram_id == 123456790))
    queried_user = result.scalar_one()

    # Assert default language is 'en'
    assert queried_user.language == "en"


@pytest.mark.asyncio
async def test_event_model_creation(async_session):
    """Test Event model creation with required fields"""
    # First create a user
    user = User(telegram_id=123456789, username="testuser", language="en")
    async_session.add(user)
    await async_session.commit()

    # Now create an event for this user
    now = datetime.datetime.now(datetime.UTC)
    event = Event(user_id=user.id, start_time=now, title="Test Event")

    # Add to session and commit
    async_session.add(event)
    await async_session.commit()

    # Query to verify
    result = await async_session.execute(select(Event).where(Event.title == "Test Event"))
    queried_event = result.scalar_one()

    # Assertions
    assert queried_event.id is not None
    assert queried_event.user_id == user.id
    assert queried_event.start_time == now
    assert queried_event.end_time is None  # Optional field not set
    assert queried_event.title == "Test Event"
    assert queried_event.is_closed is False  # Default value
    assert isinstance(queried_event.created_at, datetime.datetime)


@pytest.mark.asyncio
async def test_event_with_end_time(async_session):
    """Test Event model with end_time set"""
    # First create a user
    user = User(telegram_id=123456789, username="testuser", language="en")
    async_session.add(user)
    await async_session.commit()

    # Now create an event with end_time
    now = datetime.datetime.now(datetime.UTC)
    end = now + datetime.timedelta(hours=2)
    event = Event(user_id=user.id, start_time=now, end_time=end, title="Test Event with End Time")

    # Add to session and commit
    async_session.add(event)
    await async_session.commit()

    # Query to verify
    result = await async_session.execute(
        select(Event).where(Event.title == "Test Event with End Time")
    )
    queried_event = result.scalar_one()

    # Assertions
    assert queried_event.end_time == end


@pytest.mark.asyncio
async def test_user_events_relationship(async_session):
    """Test the relationship between User and Events"""
    # Create user
    user = User(telegram_id=123456789, username="testuser", language="en")
    async_session.add(user)
    await async_session.commit()

    # Create multiple events for the user
    now = datetime.datetime.now(datetime.UTC)
    events = [
        Event(user_id=user.id, start_time=now, title="Event 1"),
        Event(user_id=user.id, start_time=now + datetime.timedelta(days=1), title="Event 2"),
        Event(user_id=user.id, start_time=now + datetime.timedelta(days=2), title="Event 3"),
    ]

    async_session.add_all(events)
    await async_session.commit()

    # Query user with events - ADD EAGER LOADING HERE
    from sqlalchemy.orm import selectinload

    result = await async_session.execute(
        select(User).options(selectinload(User.events)).where(User.telegram_id == 123456789)
    )
    queried_user = result.scalar_one()

    # No need for refresh when using eager loading
    # await async_session.refresh(queried_user)

    # Assertions
    assert len(queried_user.events) == 3
    assert "Event 1" in [event.title for event in queried_user.events]
    assert "Event 2" in [event.title for event in queried_user.events]
    assert "Event 3" in [event.title for event in queried_user.events]


@pytest.mark.asyncio
async def test_cascade_delete(async_session):
    """Test that deleting a user cascades to delete their events"""
    # Create user
    user = User(telegram_id=123456789, username="testuser", language="en")
    async_session.add(user)
    await async_session.commit()

    # Create events for the user
    now = datetime.datetime.now(datetime.UTC)
    events = [
        Event(user_id=user.id, start_time=now, title="Event 1"),
        Event(user_id=user.id, start_time=now + datetime.timedelta(days=1), title="Event 2"),
    ]

    async_session.add_all(events)
    await async_session.commit()

    # Delete the user
    await async_session.delete(user)
    await async_session.commit()

    # Check that events were also deleted
    result = await async_session.execute(select(Event))
    remaining_events = result.scalars().all()

    # Assertions
    assert len(remaining_events) == 0


@pytest.mark.asyncio
async def test_event_is_closed_attribute(async_session):
    """Test setting and querying the is_closed flag on events"""
    # Create user
    user = User(telegram_id=123456789, username="testuser", language="en")
    async_session.add(user)
    await async_session.commit()

    # Create event
    now = datetime.datetime.now(datetime.UTC)
    event = Event(user_id=user.id, start_time=now, title="Test Event")

    async_session.add(event)
    await async_session.commit()

    # Update is_closed
    event.is_closed = True
    await async_session.commit()

    # Query to verify
    result = await async_session.execute(select(Event).where(Event.id == event.id))
    updated_event = result.scalar_one()

    # Assertions
    assert updated_event.is_closed is True


@pytest.mark.asyncio
async def test_repr_methods(async_session):
    """Test the __repr__ methods for User and Event models"""
    # Create user and event
    user = User(telegram_id=123456789, username="testuser", language="en")
    async_session.add(user)
    await async_session.commit()

    now = datetime.datetime.now(datetime.UTC)
    event = Event(user_id=user.id, start_time=now, title="Test Event")

    async_session.add(event)
    await async_session.commit()

    # Test User __repr__
    user_repr = repr(user)
    assert "User" in user_repr
    assert str(user.id) in user_repr
    assert str(user.telegram_id) in user_repr
    assert user.username in user_repr

    # Test Event __repr__
    event_repr = repr(event)
    assert "Event" in event_repr
    assert str(event.id) in event_repr
    assert event.title in event_repr
