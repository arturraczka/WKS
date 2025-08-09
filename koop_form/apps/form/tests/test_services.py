from decimal import Decimal

import pytest

from apps.form.models import OrderItem
from apps.form.services import calculate_order_cost
from django.test import TestCase

from factories.model_factories import ProductFactory, OrderItemFactory

pytestmark = pytest.mark.django_db


class CalculateOrderCostTest(TestCase):
    def setUp(self):
        # Create test products
        self.product1 = ProductFactory.create(name="Product 1", price=Decimal("10.00"))
        self.product2 = ProductFactory.create(name="Product 2", price=Decimal("20.00"))

        # Create test order items
        self.order_item1 = OrderItemFactory.create(product=self.product1, quantity=2)
        self.order_item2 = OrderItemFactory.create(product=self.product2, quantity=1)

    def test_calculate_order_cost_with_valid_items(self):
        # given
        order_items = OrderItem.objects.all()

        # when
        result = calculate_order_cost(order_items)

        # then
        expected = Decimal("40.00")
        self.assertEqual(expected, result)

    def test_calculate_order_cost_with_empty_queryset(self):
        # given
        empty_order_items = OrderItem.objects.none()

        # when
        result = calculate_order_cost(empty_order_items)

        # then
        self.assertEqual(0, result)

    def test_calculate_order_cost_with_no_quantity(self):
        # given
        order_item_zero_quantity = OrderItemFactory.create(
            product=self.product1, quantity=0
        )
        order_items = OrderItem.objects.filter(pk=order_item_zero_quantity.pk)

        # when
        result = calculate_order_cost(order_items)

        # then
        self.assertEqual(0, result)
