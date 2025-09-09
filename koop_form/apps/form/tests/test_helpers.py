from datetime import datetime, timedelta

from django.test import TestCase

from apps.core.constants import IntervalWeekdayMap
from apps.form.helpers import calculate_previous_weekday


class TestCalculatePreviousWeekday(TestCase):
    def test_custom_day_and_hour(self):
        # given
        custom_day = IntervalWeekdayMap.THURSDAY
        custom_hour = 9
        # when
        result = calculate_previous_weekday(day=custom_day, hour=custom_hour)
        expected = datetime.now().astimezone().replace(
            hour=custom_hour, minute=0, second=0, microsecond=0
        ) - timedelta(
            days=((custom_day + datetime.now().astimezone().weekday() - 1) % 7)
        )
        # then
        self.assertEqual(expected, result)

    def test_midweek_day(self):
        # given
        custom_day = IntervalWeekdayMap.FRIDAY
        custom_hour = 12
        # when
        result = calculate_previous_weekday(day=custom_day, hour=custom_hour)
        expected = datetime.now().astimezone().replace(
            hour=custom_hour, minute=0, second=0, microsecond=0
        ) - timedelta(
            days=((custom_day + datetime.now().astimezone().weekday() - 1) % 7)
        )
        # then
        self.assertEqual(expected, result)

    def test_sunday_at_midnight(self):
        # given
        custom_day = IntervalWeekdayMap.SUNDAY
        custom_hour = 0
        # when
        result = calculate_previous_weekday(day=custom_day, hour=custom_hour)
        expected = datetime.now().astimezone().replace(
            hour=custom_hour, minute=0, second=0, microsecond=0
        ) - timedelta(
            days=((custom_day + datetime.now().astimezone().weekday() - 1) % 7)
        )
        # then
        self.assertEqual(expected, result)
