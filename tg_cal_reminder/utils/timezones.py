from __future__ import annotations

from datetime import UTC, datetime, timedelta

UTC = UTC


def to_utc(dt: datetime) -> datetime:
    """Convert an aware ``datetime`` to UTC.

    Raises ``ValueError`` if ``dt`` is naive.
    """
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.astimezone(UTC)


def day_bounds(dt: datetime) -> tuple[datetime, datetime]:
    """Return start and end of the day for ``dt`` in UTC."""
    dt_utc = dt.astimezone(UTC)
    start = datetime(dt_utc.year, dt_utc.month, dt_utc.day, 0, 0, tzinfo=UTC)
    end = datetime(dt_utc.year, dt_utc.month, dt_utc.day, 23, 59, tzinfo=UTC)
    return start, end


def week_bounds(dt: datetime) -> tuple[datetime, datetime]:
    """Return Monday 00:00 and Sunday 23:59 of the ISO week of ``dt`` in UTC."""
    dt_utc = dt.astimezone(UTC)
    monday = dt_utc - timedelta(days=dt_utc.isoweekday() - 1)
    start = datetime(monday.year, monday.month, monday.day, 0, 0, tzinfo=UTC)
    sunday = start + timedelta(days=6)
    end = datetime(sunday.year, sunday.month, sunday.day, 23, 59, tzinfo=UTC)
    return start, end
