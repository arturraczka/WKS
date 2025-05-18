from decimal import Decimal

import pytest
import logging

from django.conf import settings

from apps.user.models import UserProfile
from apps.user.services import get_user_fund
from factories.model_factories import UserFactory, UserProfileFundFactory

logger = logging.getLogger("django.server")

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_profile_fund(user):
    return UserProfileFundFactory(value=Decimal("1.2"))


@pytest.fixture
def user_profile(user, user_profile_fund):
    return UserProfile(user=user, fund=user_profile_fund)


def test_get_user_fund_no_profile(user):
    user_fund = get_user_fund(user)
    assert user_fund == settings.DEFAULT_USER_FUND


def test_get_user_fund_with_profile(user, user_profile, user_profile_fund):
    user_fund = get_user_fund(user)
    assert user_fund == user_profile_fund.value
