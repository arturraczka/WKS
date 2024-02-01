import random
from decimal import Decimal

import pytest
import datetime
import logging

from django.urls import reverse
from django.test import TestCase
from django.utils import timezone

from apps.form.models import Producer, Product
from apps.form.services import (
    get_producers_list,
)
from factories.model_factories import (
    ProducerFactory,
    UserFactory,
    ProductFactory,
    OrderItemFactory,
    OrderFactory,
    ProfileFactory,
)

logger = logging.getLogger("django.server")


@pytest.mark.django_db
class TestProducerProductsReportView(TestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.client.force_login(self.user)
        self.producer = ProducerFactory()
        self.url = reverse(
            "producer-products-report", kwargs={"slug": self.producer.slug}
        )
        self.product1 = ProductFactory(
            producer=self.producer, price=5.5, name="warzywo"
        )
        self.product2 = ProductFactory(producer=self.producer, price=14, name="cebula")
        self.product3 = ProductFactory()
        OrderItemFactory(product=self.product1, quantity=Decimal(2.5))
        OrderItemFactory(product=self.product1, quantity=Decimal(2))
        OrderItemFactory(product=self.product2, quantity=Decimal(5))
        OrderItemFactory(product=self.product2, quantity=Decimal(0.5))
        OrderItemFactory(product=self.product3)
        OrderItemFactory(product=self.product3)
        number = random.randint(8, 20)
        past_date = timezone.now() - datetime.timedelta(days=number)
        item = OrderItemFactory(product=self.product1)
        item.item_ordered_date = past_date
        item.save()

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        assert response.status_code == 200
        assert context_data["producer"] == self.producer
        assert context_data["producers"] == get_producers_list(Producer)
        assert sorted(context_data["product_names_list"]) == ["cebula", "warzywo"]
        assert sorted(context_data["product_ordered_quantities_list"]) == [4.5, 5.5]
        assert sorted(context_data["product_incomes_list"]) == ["24.75", "77.00"]
        assert context_data["total_income"] == 101.75

    def test_user_is_not_staff(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        assert response.status_code == 302


@pytest.mark.django_db
class TestProducerBoxReportView(TestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.client.force_login(self.user)
        self.producer = ProducerFactory()
        self.url = reverse("producer-box-report", kwargs={"slug": self.producer.slug})
        for _ in range(5):
            ProductFactory()
            ProducerFactory()
        self.orderitem1 = OrderItemFactory(
            product=ProductFactory(name="Alaska", producer=self.producer), quantity=4
        )
        self.orderitem2 = OrderItemFactory(
            product=ProductFactory(name="Barabasz", producer=self.producer), quantity=1
        )
        self.orderitem3 = OrderItemFactory(
            product=ProductFactory(name="Celuloza", producer=self.producer), quantity=2
        )

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        products = Product.objects.filter(orderitems__isnull=False)
        producers = Producer.objects.filter(is_active=True).values("slug", "name")
        producers = [[producer["slug"], producer["name"]] for producer in producers]

        assert context_data["producer"] == self.producer
        assert list(context_data["producers"]) == list(producers)
        assert list(context_data["products"]) == list(products)
        assert list(context_data["order_data"]) == [
            "(skrz1: 4) ",
            "(skrz2: 1) ",
            "(skrz3: 2) ",
        ]
        assert response.status_code == 200

    def test_user_is_not_staff(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        assert response.status_code == 302


@pytest.mark.django_db
class TestUsersReportView(TestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.client.force_login(self.user)
        self.url = reverse("users-report")

        self.user1 = UserFactory(first_name="Kamil", last_name="K")
        self.user2 = UserFactory(first_name="Marek", last_name="M")
        self.user3 = UserFactory(first_name="Wojtek", last_name="W")
        ProfileFactory(koop_id=1, user=self.user1, phone_number=444555666)
        ProfileFactory(koop_id=2, user=self.user2, phone_number=777666555)
        OrderFactory(user=self.user1, pick_up_day="środa")
        OrderFactory(user=self.user2, pick_up_day="czwartek")

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        assert response.status_code == 200
        assert context_data["user_name_list"] == ["K Kamil", "M Marek"]
        assert context_data["user_order_number_list"] == [1, 2]
        assert context_data["user_pickup_day_list"] == ["środa", "czwartek"]
        assert context_data["user_phone_number_list"] == [444555666, 777666555]

    def test_user_is_not_staff(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        assert response.status_code == 302


@pytest.mark.django_db
class TestProducerProductsListView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        for _ in range(
            0,
            5,
        ):
            ProducerFactory()
        self.url = reverse("producer-products-list")

    def test_user_is_not_staff(self):
        response = self.client.get(self.url)

        assert response.status_code == 302

    def test_response_and_context(self):
        user = UserFactory(is_staff=True)
        self.client.force_login(user)
        response = self.client.get(self.url)
        context_data = response.context
        producers_query = Producer.objects.filter(is_active=True).values("slug", "name")
        producers = [
            [producer["slug"], producer["name"]] for producer in producers_query
        ]

        assert response.status_code == 200
        assert list(context_data["producers"]) == producers


class TestProducerBoxListView(TestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.client.force_login(self.user)
        self.url = reverse("producer-box-list")

    def test_response(self):
        response = self.client.get(self.url)

        assert response.status_code == 200
