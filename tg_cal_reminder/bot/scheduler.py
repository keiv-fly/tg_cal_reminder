from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

# Europe/Paris timezone used for all digests
PARIS_TZ = ZoneInfo("Europe/Paris")


async def morning_digest() -> None:
    """Placeholder morning digest task."""
    # TODO: implement sending morning digest to users
    return None


async def evening_digest() -> None:
    """Placeholder evening digest task."""
    # TODO: implement sending evening digest to users
    return None


async def weekly_digest() -> None:
    """Placeholder weekly digest task."""
    # TODO: implement sending weekly digest to users
    return None


def create_scheduler() -> AsyncIOScheduler:
    """Return an ``AsyncIOScheduler`` pre-configured with digest jobs."""
    scheduler = AsyncIOScheduler(timezone=PARIS_TZ)
    scheduler.add_job(morning_digest, CronTrigger(hour=8, minute=0, timezone=PARIS_TZ), id="morning_digest")
    scheduler.add_job(evening_digest, CronTrigger(hour=19, minute=0, timezone=PARIS_TZ), id="evening_digest")
    scheduler.add_job(
        weekly_digest,
        CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=PARIS_TZ),
        id="weekly_digest",
    )
    return scheduler


# --- Time window helpers ----------------------------------------------------

def _day_window(target: date) -> Tuple[datetime, datetime]:
    start_local = datetime.combine(target, time.min, tzinfo=PARIS_TZ)
    end_local = datetime.combine(target, time(23, 59, 59), tzinfo=PARIS_TZ)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def morning_window(now: datetime | None = None) -> Tuple[datetime, datetime]:
    now = now.astimezone(PARIS_TZ) if now else datetime.now(PARIS_TZ)
    return _day_window(now.date())


def evening_window(now: datetime | None = None) -> Tuple[datetime, datetime]:
    now = now.astimezone(PARIS_TZ) if now else datetime.now(PARIS_TZ)
    tomorrow = now.date() + timedelta(days=1)
    return _day_window(tomorrow)


def weekly_window(now: datetime | None = None) -> Tuple[datetime, datetime]:
    now = now.astimezone(PARIS_TZ) if now else datetime.now(PARIS_TZ)
    weekday = now.isoweekday()
    monday = now.date() - timedelta(days=weekday - 1)
    sunday = monday + timedelta(days=6)
    start_local = datetime.combine(monday, time.min, tzinfo=PARIS_TZ)
    end_local = datetime.combine(sunday, time(23, 59, 59), tzinfo=PARIS_TZ)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)
