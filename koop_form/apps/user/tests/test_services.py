from decimal import Decimal

import pytest
import logging

from django.conf import settings

from apps.form.services import display_as_zloty
from apps.user.services import get_user_fund

logger = logging.getLogger("django.server")

pytestmark = pytest.mark.django_db


def test_get_user_fund_no_profile(user):
    user_fund = get_user_fund(user)
    assert user_fund == settings.DEFAULT_USER_FUND


def test_get_user_fund_with_profile(user, user_profile):
    user_fund = get_user_fund(user)
    assert user_fund == user_profile.fund.value


@pytest.mark.parametrize(
    "input_value, expected",
    [
        (Decimal("10"), "10,0 zł"),
        (Decimal("0"), "0,0 zł"),
        (Decimal("1234.56"), "1234,6 zł"),
        (Decimal("-5.5"), "-5,5 zł"),
    ],
)
def test_display_as_zloty(input_value, expected):
    assert display_as_zloty(input_value) == expected
