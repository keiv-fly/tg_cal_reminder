import datetime

import pytest

from tg_cal_reminder.utils.parser import (
    EventParseError,
    parse_event_line,
)


@pytest.mark.parametrize(
    "line, expected_utc",
    [
        (
            "2025-05-20 14:00 Dentist",
            (datetime.datetime(2025, 5, 20, 14, 0, tzinfo=datetime.UTC), None, "Dentist"),
        ),
        (
            "2025-12-31 23:00 2026-01-01 01:00 Party",
            (
                datetime.datetime(2025, 12, 31, 23, 0, tzinfo=datetime.UTC),
                datetime.datetime(2026, 1, 1, 1, 0, tzinfo=datetime.UTC),
                "Party",
            ),
        ),
    ],
)
def test_parse_valid(line, expected_utc):
    assert parse_event_line(line) == expected_utc


def test_invalid_date():
    with pytest.raises(EventParseError) as err:
        parse_event_line("2025-13-01 10:00 Bad date")
    assert err.value.token == "date"


def test_invalid_time():
    with pytest.raises(EventParseError) as err:
        parse_event_line("2025-12-01 25:00 Bad time")
    assert err.value.token == "time"


def test_missing_title():
    with pytest.raises(EventParseError) as err:
        parse_event_line("2025-12-01 10:00")
    assert err.value.token == "title"
