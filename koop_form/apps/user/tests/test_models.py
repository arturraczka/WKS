import pytest
from apps.form.tests.factories import (
    UserFactory,
)
from django.test import TestCase

from apps.user.models import UserProfile


class TestUserProfile(TestCase):
    def setUp(self):
        UserFactory()

    def test_signal_create_user_profile(self):
        profile_count = UserProfile.objects.count()
        assert profile_count == 1
