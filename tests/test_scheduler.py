import datetime

from apscheduler.triggers.cron import CronTrigger

from tg_cal_reminder.bot.scheduler import (
    create_scheduler,
    evening_window,
    morning_window,
    weekly_window,
)


def test_create_scheduler_jobs() -> None:
    scheduler = create_scheduler()
    job_ids = {job.id for job in scheduler.get_jobs()}
    assert job_ids == {"morning_digest", "evening_digest", "weekly_digest"}

    morning = scheduler.get_job("morning_digest")
    assert isinstance(morning.trigger, CronTrigger)
    assert str(morning.trigger.fields[5].expressions[0]) == "6"
    assert str(morning.trigger.fields[6].expressions[0]) == "0"
    assert morning.trigger.timezone == datetime.UTC

    evening = scheduler.get_job("evening_digest")
    assert isinstance(evening.trigger, CronTrigger)
    assert str(evening.trigger.fields[5].expressions[0]) == "17"
    assert str(evening.trigger.fields[6].expressions[0]) == "0"

    weekly = scheduler.get_job("weekly_digest")
    assert isinstance(weekly.trigger, CronTrigger)
    assert str(weekly.trigger.fields[4].expressions[0]) == "mon"


def test_digest_time_windows() -> None:
    sample = datetime.datetime(2024, 3, 6, 12, 0, tzinfo=datetime.UTC)

    start, end = morning_window(sample)
    assert start == datetime.datetime(2024, 3, 6, 0, 0, tzinfo=datetime.UTC)
    assert end == datetime.datetime(2024, 3, 6, 23, 59, 59, tzinfo=datetime.UTC)

    start, end = evening_window(sample)
    assert start == datetime.datetime(2024, 3, 7, 0, 0, tzinfo=datetime.UTC)
    assert end == datetime.datetime(2024, 3, 7, 23, 59, 59, tzinfo=datetime.UTC)

    start, end = weekly_window(sample)
    assert start == datetime.datetime(2024, 3, 4, 0, 0, tzinfo=datetime.UTC)
    assert end == datetime.datetime(2024, 3, 10, 23, 59, 59, tzinfo=datetime.UTC)
