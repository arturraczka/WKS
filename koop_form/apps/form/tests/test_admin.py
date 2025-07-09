from decimal import Decimal

import pytest

from apps.form.admin import OrderAdmin
from apps.form.models import Order
from factories.model_factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestOrderAdmin:
    @pytest.fixture(autouse=True)
    def _setup(self, admin_user, request_factory, admin_site):
        self.model_admin = OrderAdmin(Order, admin_site)
        self.request = request_factory.post("")
        self.request.user = admin_user
        self.return_format = "{:.2f} zł"

    def test_user_balance_method(self, user, user_profile, order):
        assert self.model_admin.user_balance(order) == self.return_format.format(order.user_balance)

    def test_order_cost_with_fund_method(self, user, user_profile, order):
        assert self.model_admin.order_cost_with_fund(order) == self.return_format.format(order.order_cost_with_fund)

    def test_save_model_assigns_order_number(self, user):
        OrderFactory()
        OrderFactory()
        order = OrderFactory.build(order_number=None, user=user)
        order.paid_amount = None
        self.model_admin.save_model(self.request, order, form=None, change=False)

        order.refresh_from_db()
        expected_order_number = 3
        assert order.order_number == expected_order_number

    def test_update_user_balance_db_paid_equals_new_paid(self, user, user_profile, order):
        old_balance = user_profile.payment_balance
        old_paid = order.paid_amount
        new_paid = old_paid
        order.paid_amount = new_paid
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert user_profile.payment_balance == old_balance

    def test_update_user_balance_new_paid(self, user, user_profile, order):
        old_balance = user_profile.payment_balance
        old_paid = order.paid_amount
        new_paid = Decimal("50")
        paid_delta = new_paid - old_paid
        order.paid_amount = new_paid
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert order.paid_amount == new_paid
        assert user_profile.payment_balance == old_balance + paid_delta

    def test_update_user_balance_old_paid_is_none(self, user, user_profile, order):
        old_balance = user_profile.payment_balance
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        new_paid = Decimal("50")
        order.paid_amount = new_paid
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert user_profile.payment_balance == order.order_balance + old_balance

    def test_update_user_balance_new_paid_is_none(self, user, user_profile, order):
        old_paid = order.paid_amount
        old_balance = user_profile.payment_balance
        order.paid_amount = None
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert user_profile.payment_balance == old_balance - old_paid + order.order_cost_with_fund

    # TODO
    def test_is_settled_method(self):
        pass

    # TODO
    def test_user_fund_method(self):
        pass

    # TODO
    def test_order_cost_method(self):
        pass

    # TODO
    def test_user_and_order_balance_method(self):
        pass

    # TODO
    def test_delete_model_method(self):
        pass

    # TODO
    def test_delete_queryset_method(self):
        pass
