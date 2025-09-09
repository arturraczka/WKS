from django.test import TestCase

from apps.form.models import WeightScheme


# first we have to run database: make run-only-database
class SimpleTest(TestCase):
    def test_simple(self):
        # when
        result = WeightScheme.objects.filter(quantity=0).first()

        # then
        self.assertTrue(result)
