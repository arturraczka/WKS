from decimal import Decimal

import pytest


@pytest.mark.django_db
class TestApplyOrderBalance:
    def test_positive_value(self, user_profile):
        user_profile.payment_balance = Decimal("0.00")
        user_profile.apply_order_balance(Decimal("50.00"))
        assert user_profile.payment_balance == Decimal("50.00")

    def test_negative_value(self, user_profile):
        user_profile.payment_balance = Decimal("100.00")
        user_profile.apply_order_balance(Decimal("-25.00"))
        assert user_profile.payment_balance == Decimal("75.00")

    def test_zero_value(self, user_profile):
        user_profile.payment_balance = Decimal("20.00")
        user_profile.apply_order_balance(Decimal("0.00"))
        assert user_profile.payment_balance == Decimal("20.00")
