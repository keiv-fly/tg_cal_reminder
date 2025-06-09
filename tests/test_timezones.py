import datetime

import pytest

from tg_cal_reminder.utils.timezones import (
    UTC,
    day_bounds,
    to_utc,
    week_bounds,
)


def test_constants():
    assert UTC is datetime.UTC


def test_to_utc_conversion():
    tz = datetime.timezone(datetime.timedelta(hours=1))
    dt_local = datetime.datetime(2024, 1, 1, 13, 0, tzinfo=tz)
    converted = to_utc(dt_local)
    assert converted.hour == 12
    assert converted.tzinfo is datetime.UTC


def test_to_utc_rejects_naive():
    with pytest.raises(ValueError):
        to_utc(datetime.datetime(2024, 1, 1, 12, 0))


def test_day_bounds():
    dt = datetime.datetime(2024, 1, 5, 15, 30, tzinfo=UTC)
    start, end = day_bounds(dt)
    assert start == datetime.datetime(2024, 1, 5, 0, 0, tzinfo=UTC)
    assert end == datetime.datetime(2024, 1, 5, 23, 59, tzinfo=UTC)


def test_week_bounds():
    dt = datetime.datetime(2024, 1, 5, 12, 0, tzinfo=UTC)  # Friday
    start, end = week_bounds(dt)
    assert start == datetime.datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    assert end == datetime.datetime(2024, 1, 7, 23, 59, tzinfo=UTC)
