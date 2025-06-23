import pytest
import logging

from django.conf import settings

from apps.user.services import get_user_fund

logger = logging.getLogger("django.server")

pytestmark = pytest.mark.django_db


def test_get_user_fund_no_profile(user):
    user_fund = get_user_fund(user)
    assert user_fund == settings.DEFAULT_USER_FUND


def test_get_user_fund_with_profile(user, user_profile):
    user_fund = get_user_fund(user)
    assert user_fund == user_profile.fund.value
