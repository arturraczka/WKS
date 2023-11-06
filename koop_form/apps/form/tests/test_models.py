import datetime

import pytest
from django.db.models import Q
from apps.form.models import OrderItem, Product, Order
from apps.form.services import calculate_previous_friday
from apps.form.tests.factories import (
    UserFactory,
    ProductFactory,
    OrderItemFactory,
    OrderFactory, ProducerFactory,
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

        product_db = Product.objects.get(id=self.product.id)
        product_db.quantity_delivered_this_week = random.randint(7, 12)
        product_db.save()

        assert ordered_quantity > product_db.quantity_delivered_this_week

        ordered_quantity = self.calculate_ordered_quantity(previous_friday)

        assert ordered_quantity <= product_db.quantity_delivered_this_week


@pytest.mark.django_db
class TestOrderModel(TestCase):
    def setUp(self):
        for _ in range(1, 20):
            number = random.randint(1, 20)
            past_date = datetime.datetime.now() - datetime.timedelta(days=number)
            OrderFactory(date_created=past_date)

    def test_calculate_order_number(self):
        previous_friday = calculate_previous_friday()
        orders_qs = Order.objects.filter(date_created__gte=previous_friday).order_by('date_created')

        initial_number = 0
        for order in orders_qs:
            initial_number += 1
            assert order.order_number == initial_number

    def test_recalculate_order_numbers(self):
        previous_friday = calculate_previous_friday()
        qs_count = Order.objects.filter(date_created__gte=previous_friday).count()
        rand_int = random.randint(0, qs_count - 1)
        list(Order.objects.filter(date_created__gte=previous_friday))[rand_int].delete()

        self.test_calculate_order_number()


@pytest.mark.django_db
class TestOrderItemModel(TestCase):
    def setUp(self):
        self.orderitem = OrderItemFactory()

    def test_quantity_eq_0_triggers_delete(self):
        orderitem_qs_count = OrderItem.objects.filter().count()
        assert orderitem_qs_count == 1

        self.orderitem.quantity = 0
        self.orderitem.save()

        orderitem_qs_count = OrderItem.objects.filter().count()
        assert orderitem_qs_count == 0


@pytest.mark.django_db
class TestProducerModel(TestCase):
    def setUp(self):
        self.producer = ProducerFactory(name='Wielka! Korba p.13')

    def test_slug_creation(self):
        assert self.producer.slug == 'wielka-korba-p13'
