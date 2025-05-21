import datetime

import pytest

from tg_cal_reminder.utils.timezones import (
    PARIS,
    UTC,
    day_bounds,
    to_paris,
    to_utc,
    week_bounds,
)


def test_constants():
    assert PARIS.key == "Europe/Paris"
    assert UTC is datetime.UTC


def test_to_paris_and_to_utc_roundtrip():
    dt_utc = datetime.datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    dt_paris = to_paris(dt_utc)
    assert dt_paris.tzinfo == PARIS
    assert dt_paris.hour == 13  # UTC+1 in January
    assert to_utc(dt_paris) == dt_utc


def test_to_utc_rejects_naive():
    with pytest.raises(ValueError):
        to_utc(datetime.datetime(2024, 1, 1, 12, 0))


def test_day_bounds():
    dt = datetime.datetime(2024, 1, 5, 15, 30, tzinfo=UTC)
    start, end = day_bounds(dt)
    assert start == datetime.datetime(2024, 1, 5, 0, 0, tzinfo=PARIS)
    assert end == datetime.datetime(2024, 1, 5, 23, 59, tzinfo=PARIS)


def test_week_bounds():
    dt = datetime.datetime(2024, 1, 5, 12, 0, tzinfo=PARIS)  # Friday
    start, end = week_bounds(dt)
    assert start == datetime.datetime(2024, 1, 1, 0, 0, tzinfo=PARIS)
    assert end == datetime.datetime(2024, 1, 7, 23, 59, tzinfo=PARIS)
