from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


async def morning_digest() -> None:
    """Placeholder morning digest task."""
    # TODO: implement sending morning digest to users
    return


async def evening_digest() -> None:
    """Placeholder evening digest task."""
    # TODO: implement sending evening digest to users
    return


async def weekly_digest() -> None:
    """Placeholder weekly digest task."""
    # TODO: implement sending weekly digest to users
    return


def create_scheduler() -> AsyncIOScheduler:
    """Return an ``AsyncIOScheduler`` pre-configured with digest jobs."""
    scheduler = AsyncIOScheduler(timezone=UTC)
    scheduler.add_job(
        morning_digest, CronTrigger(hour=6, minute=0, timezone=UTC), id="morning_digest"
    )
    scheduler.add_job(
        evening_digest, CronTrigger(hour=17, minute=0, timezone=UTC), id="evening_digest"
    )
    scheduler.add_job(
        weekly_digest,
        CronTrigger(day_of_week="mon", hour=6, minute=0, timezone=UTC),
        id="weekly_digest",
    )
    return scheduler


# --- Time window helpers ----------------------------------------------------


def _day_window(target: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(target, time.min, tzinfo=PARIS_TZ)
    end_local = datetime.combine(target, time(23, 59, 59), tzinfo=PARIS_TZ)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def morning_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now.astimezone(PARIS_TZ) if now else datetime.now(PARIS_TZ)
    return _day_window(now.date())


def evening_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now.astimezone(PARIS_TZ) if now else datetime.now(PARIS_TZ)
    tomorrow = now.date() + timedelta(days=1)
    return _day_window(tomorrow)


def weekly_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now.astimezone(PARIS_TZ) if now else datetime.now(PARIS_TZ)
    weekday = now.isoweekday()
    monday = now.date() - timedelta(days=weekday - 1)
    sunday = monday + timedelta(days=6)
    start_local = datetime.combine(monday, time.min, tzinfo=PARIS_TZ)
    end_local = datetime.combine(sunday, time(23, 59, 59), tzinfo=PARIS_TZ)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)
