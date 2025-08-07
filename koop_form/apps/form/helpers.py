from datetime import datetime, timedelta


def calculate_previous_weekday(day=3, hour=1):
    """Returns datetime object of a chosen day of a week within last 7 days. Defaults to Saturday 1:00 AM. Monday: 1, Tuesday: 7, Wednesday: 6,
    Thursday: 5, Friday: 4, Saturday: 3, Sunday: 2"""
    today = (
        datetime.now()
        .astimezone()
        .replace(hour=hour, minute=0, second=0, microsecond=0)
    )
    weekday = day
    days_until_previous_day = (weekday + today.weekday() - 1) % 7
    return today - timedelta(days=days_until_previous_day)


def koop_default_interval_start():
    return calculate_previous_weekday()
