import pytest
from django.db.models import Q
from apps.form.models import OrderItem, Product, Order
from apps.form.services import calculate_previous_friday
from apps.form.tests.factories import (
    UserFactory,
    ProductFactory,
    OrderItemFactory,
    OrderFactory,
)
from django.test import TestCase
import logging
import random

logger = logging.getLogger("django.server")


@pytest.mark.django_db
class TestProductModel(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.order = OrderFactory(user=self.user)
        self.product = ProductFactory(order_max_quantity=100)

    def calculate_ordered_quantity(self, previous_friday):
        orderitems = (
            OrderItem.objects.filter(product=self.product.id)
            .filter(Q(item_ordered_date__gte=previous_friday))
            .order_by("item_ordered_date")
        )

        ordered_quantity = 0
        for item in orderitems:
            ordered_quantity += item.quantity

        return ordered_quantity

    def test_reduce_order_quantity(self):
        previous_friday = calculate_previous_friday()
        OrderItemFactory(product=self.product, quantity=5)
        for _ in range(1, 8):
            OrderItemFactory(product=self.product)

        ordered_quantity = self.calculate_ordered_quantity(previous_friday)
        logger.info(ordered_quantity)

        product_db = Product.objects.get(id=self.product.id)
        product_db.quantity_delivered_this_week = random.randint(7, 12)
        logger.info(product_db.quantity_delivered_this_week)
        product_db.save()

        assert ordered_quantity > product_db.quantity_delivered_this_week

        ordered_quantity = self.calculate_ordered_quantity(previous_friday)
        logger.info(ordered_quantity)

        assert ordered_quantity <= product_db.quantity_delivered_this_week


@pytest.mark.django_db
class TestOrderModel(TestCase):
    def setUp(self):
        for _ in range(5, random.randint(10, 20)):
            OrderFactory()

    def test_calculate_order_number(self):
        previous_friday = calculate_previous_friday()
        orders_qs = Order.objects.filter(date_created__gte=previous_friday).order_by('date_created')

        initial_number = 0
        for order in orders_qs:
            initial_number += 1
            logger.info(order.order_number)
            assert order.order_number == initial_number

    def test_recalculate_order_numbers(self):
        previous_friday = calculate_previous_friday()
        qs_count = Order.objects.filter(date_created__gte=previous_friday).count()
        rand_int = random.randint(0, qs_count - 1)
        list(Order.objects.filter(date_created__gte=previous_friday))[rand_int].delete()

        self.test_calculate_order_number()
