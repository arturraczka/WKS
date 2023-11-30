import datetime
import pytest
import random
import logging

from django.db.models import Q
from django.test import TestCase

from apps.form.models import OrderItem, Product, Order, WeightScheme
from apps.form.services import calculate_previous_day
from factories.model_factories import (
    UserFactory,
    ProductFactory,
    OrderItemFactory,
    OrderFactory,
    ProducerFactory,
)

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
        previous_friday = calculate_previous_day(4, 10)
        OrderItemFactory(product=self.product, quantity=5)
        for _ in range(1, 8):
            OrderItemFactory(product=self.product)

        ordered_quantity = self.calculate_ordered_quantity(previous_friday)

        product_db = Product.objects.get(id=self.product.id)
        rand_quantity = random.randint(7, 12)
        product_db.quantity_delivered_this_week = rand_quantity
        product_db.save()

        ordered_quantity_post_save = self.calculate_ordered_quantity(previous_friday)

        assert product_db.quantity_delivered_this_week == -1
        assert ordered_quantity > rand_quantity
        assert ordered_quantity_post_save <= rand_quantity

    def test_signal_add_zero_as_weight_scheme(self):
        zero_weight_scheme = WeightScheme.objects.get(quantity=0)
        assert zero_weight_scheme in list(self.product.weight_schemes.all())


@pytest.mark.django_db
class TestOrderModel(TestCase):
    def setUp(self):
        for _ in range(1, 20):
            number = random.randint(1, 20)
            past_date = datetime.datetime.now().astimezone() - datetime.timedelta(
                days=number
            )
            OrderFactory(date_created=past_date)

    def test_calculate_order_number(self):
        previous_friday = calculate_previous_day(4, 10)
        orders_qs = Order.objects.filter(date_created__gte=previous_friday).order_by(
            "date_created"
        )

        initial_number = 0
        for order in orders_qs:
            initial_number += 1
            assert order.order_number == initial_number

    def test_recalculate_order_numbers(self):
        previous_friday = calculate_previous_day(4, 10)
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
        self.producer = ProducerFactory(name="Wielka! Korba p.13")

        for _ in range(0, 5):
            product = ProductFactory(producer=self.producer)
            for _ in range(0, 3):
                OrderItemFactory(product=product)

    def test_slug_creation(self):
        assert self.producer.slug == "wielka-korba-p13"

    def test_set_products_quantity_to_0(self):
        count_pre_save = OrderItem.objects.count()

        self.producer.not_arrived = True
        self.producer.save()

        products_qs = Product.objects.filter(producer=self.producer)
        count_post_save = OrderItem.objects.count()

        assert self.producer.not_arrived is False
        for product in products_qs:
            assert product.quantity_delivered_this_week == -1
        assert count_pre_save == 15
        assert count_post_save == 0

    def test_switch_products_isactive_bool_value(self):
        self.producer.is_active = False
        self.producer.save()

        products_qs = Product.objects.filter(producer=self.producer)
        for product in products_qs:
            assert product.is_active is False

        self.producer.is_active = True
        self.producer.save()

        products_qs = Product.objects.filter(producer=self.producer)
        for product in products_qs:
            assert product.is_active is True
