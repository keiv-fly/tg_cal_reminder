from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
UTC = UTC


def to_utc(dt: datetime) -> datetime:
    """Convert an aware ``datetime`` to UTC.

    Raises ``ValueError`` if ``dt`` is naive.
    """
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.astimezone(UTC)


def to_paris(dt: datetime) -> datetime:
    """Convert an aware ``datetime`` to Europe/Paris timezone.

    Raises ``ValueError`` if ``dt`` is naive.
    """
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.astimezone(PARIS)


def day_bounds(dt: datetime) -> tuple[datetime, datetime]:
    """Return start and end of the day for ``dt`` in Europe/Paris."""
    local = dt.astimezone(PARIS)
    start = datetime(local.year, local.month, local.day, 0, 0, tzinfo=PARIS)
    end = datetime(local.year, local.month, local.day, 23, 59, tzinfo=PARIS)
    return start, end


def week_bounds(dt: datetime) -> tuple[datetime, datetime]:
    """Return Monday 00:00 and Sunday 23:59 of the ISO week of ``dt`` in Paris."""
    local = dt.astimezone(PARIS)
    monday = local - timedelta(days=local.isoweekday() - 1)
    start = datetime(monday.year, monday.month, monday.day, 0, 0, tzinfo=PARIS)
    sunday = start + timedelta(days=6)
    end = datetime(sunday.year, sunday.month, sunday.day, 23, 59, tzinfo=PARIS)
    return start, end
