from datetime import timedelta

import pytest
from django.utils import timezone

from apps.form.models import Order
from factories.model_factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestOrderManager:
    def test_filter_this_week_orders(self):
        before_previous_friday = timezone.now() - timedelta(days=8)
        later_order = OrderFactory()
        later_order.date_created = before_previous_friday
        later_order.save(update_fields=["date_created"])
        earlier_order = OrderFactory()
        orders = Order.objects.filter_this_week_orders()
        assert len(orders) == 1
        assert later_order not in orders
        assert earlier_order in orders
