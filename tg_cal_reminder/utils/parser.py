from __future__ import annotations

import datetime as dt
import re
from datetime import UTC

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
TIME_RE = re.compile(r"\d{2}:\d{2}")


class EventParseError(ValueError):
    """Raised when an event string cannot be parsed."""

    def __init__(self, token: str):
        super().__init__(token)
        self.token = token


def _parse_date(token: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(token, "%Y-%m-%d")
    except ValueError as exc:  # invalid date
        raise EventParseError("date") from exc


def _parse_time(token: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(token, "%H:%M")
    except ValueError as exc:  # invalid time
        raise EventParseError("time") from exc


def parse_event_line(
    line: str, tzinfo: dt.tzinfo = UTC,
) -> tuple[dt.datetime, dt.datetime | None, str]:
    """Parse ``line`` into start time, optional end time and title.

    Datetimes are returned in UTC.
    """
    if ";" in line:
        raise EventParseError("title")

    parts = line.strip().split()
    if len(parts) < 3:
        raise EventParseError("title")

    start_date = _parse_date(parts[0])
    start_time_part = _parse_time(parts[1])
    start_naive = dt.datetime.combine(start_date.date(), start_time_part.time())
    start = start_naive.replace(tzinfo=tzinfo).astimezone(UTC)

    idx = 2
    end: dt.datetime | None = None
    if len(parts) >= 4 and DATE_RE.fullmatch(parts[2]) and TIME_RE.fullmatch(parts[3]):
        end_date = _parse_date(parts[2])
        end_time_part = _parse_time(parts[3])
        end_naive = dt.datetime.combine(end_date.date(), end_time_part.time())
        end = end_naive.replace(tzinfo=tzinfo).astimezone(UTC)
        idx = 4

    if len(parts) <= idx:
        raise EventParseError("title")
    title = " ".join(parts[idx:])
    return start, end, title
