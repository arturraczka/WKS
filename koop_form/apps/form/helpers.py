from datetime import datetime, timedelta
from django.conf import settings


def calculate_previous_weekday(day: int = 3, hour: int = 1) -> datetime:
    """Returns a datetime object of a chosen day of a week within the last 7 days. Defaults to Saturday 1:00 AM. Monday: 1, Tuesday: 7, Wednesday: 6,
    Thursday: 5, Friday: 4, Saturday: 3, Sunday: 2"""
    today = (
        datetime.now()
        .astimezone()
        .replace(hour=hour, minute=0, second=0, microsecond=0)
    )
    weekday = day
    days_until_previous_day = (weekday + today.weekday() - 1) % 7
    return today - timedelta(days=days_until_previous_day)


def koop_default_interval_start() -> datetime:
    return calculate_previous_weekday(
        day=settings.KOOP_WEEK_INTERVAL_START_WEEKDAY,
        hour=settings.KOOP_WEEK_INTERVAL_START_HOUR,
    )
