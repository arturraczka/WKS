import random
import pytest
from django.urls import reverse
import datetime

from django.utils import timezone

from apps.form.models import Order, OrderItem, Producer, Product
from apps.form.services import list_messages, calculate_available_quantity
from factories.model_factories import (
    ProducerFactory,
    UserFactory,
    WeightSchemeFactory,
    ProductFactory,
    OrderWithProductFactory,
    OrderItemFactory,
    OrderFactory, ProfileFactory,
)
from django.test import TestCase
import logging

logger = logging.getLogger("django.server")


@pytest.mark.django_db
class TestProducersView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        for _ in range(
            0,
            5,
        ):
            ProducerFactory()
        self.url = reverse("producers")

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context
        producers_query = Producer.objects.filter(is_active=True).values("slug", "name")
        producers = [
            [producer["slug"], producer["name"]] for producer in producers_query
        ]

        assert response.status_code == 200
        assert list(context_data["producers"]) == producers

    def test_get_queryset(self):
        pre_create_producer_count = Producer.objects.count()
        for _ in range(
            0,
            5,
        ):
            ProducerFactory(is_active=False)

        response = self.client.get(self.url)

        context_data = response.context
        context_producer_count = len(context_data["producers"])

        assert pre_create_producer_count == context_producer_count


@pytest.mark.django_db
class TestProductsView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.producer = ProducerFactory()
        for _ in range(0, 5):
            ProductFactory(producer=self.producer)
            ProductFactory()
        self.url = reverse("products", kwargs={"slug": self.producer.slug})

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        products_with_related = list(
            Product.objects.filter(producer=self.producer.id)
            .filter(is_active=True)
            .prefetch_related("weight_schemes", "statuses")
        )
        producer = Producer.objects.get(pk=self.producer.id)
        producers_query = Producer.objects.filter(is_active=True).values("slug", "name")
        producers = [
            [producer["slug"], producer["name"]] for producer in producers_query
        ]

        assert response.status_code == 200
        assert context_data["producer"] == producer
        assert list(context_data["products_with_related"]) == products_with_related
        assert list(context_data["producers"]) == producers


def get_test_data(context_data, product):
    orderitem_qs = OrderItem.objects.filter(product=product)
    quantity = 0

    for item in orderitem_qs:
        quantity += item.quantity

    income = quantity * product.price
    product_context = context_data["products"].get(id=product.id)
    return quantity, income, product_context


@pytest.mark.django_db
class TestProducerProductsReportView(TestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.client.force_login(self.user)
        self.producer = ProducerFactory()
        self.url = reverse("producer-products-report", kwargs={"slug": self.producer.slug})
        self.product1 = ProductFactory(producer=self.producer)
        self.product2 = ProductFactory(producer=self.producer)
        self.product3 = ProductFactory()
        for _ in range(0, 5):
            OrderItemFactory(product=self.product1)
            OrderItemFactory(product=self.product2)
            number = random.randint(7, 20)
            past_date = timezone.now() - datetime.timedelta(days=number)
            OrderItemFactory(item_ordered_date=past_date)

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        product1_ordered_quantity, product1_income, product1 = get_test_data(
            context_data, self.product1
        )
        product2_ordered_quantity, product2_income, product2 = get_test_data(
            context_data, self.product2
        )
        total_income = product1_income + product2_income

        assert response.status_code == 200
        assert product1.ordered_quantity == product1_ordered_quantity
        assert product1.income == product1_income
        assert product2.ordered_quantity == product2_ordered_quantity
        assert product2.income == product2_income
        assert context_data["total_income"] == total_income
        assert self.product1 in list(context_data["products"])
        assert self.product2 in list(context_data["products"])
        assert self.product3 not in list(context_data["products"])

    def test_user_is_not_staff(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        assert response.status_code == 302


@pytest.mark.django_db
class TestOrderProducersView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.producer = ProducerFactory()
        self.order = OrderFactory(user=self.user)
        self.url = reverse("order-producers")

    def test_response(self):
        response = self.client.get(self.url)

        assert response.status_code == 200

    def test_test_func(self):
        Order.objects.get(pk=self.order.id).delete()
        response = self.client.get(self.url)

        assert response.status_code == 302


@pytest.mark.django_db
class TestOrderProductsFormView(TestCase):
    def setUp(self):
        self.producer = ProducerFactory()
        self.url = reverse("order-products-form", kwargs={"slug": self.producer.slug})
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.weight_scheme_list = [
            WeightSchemeFactory(quantity=val)
            for val in [0.000, 0.500, 1.000, 2.000, 3.000, 4.000, 5.000]
        ]
        self.product1 = ProductFactory(
            producer=self.producer,
            weight_schemes=self.weight_scheme_list,
            order_max_quantity=10,
        )
        for _ in range(0, 3):
            ProductFactory(producer=self.producer, is_active=False)
        self.order = OrderWithProductFactory(user=self.user)

    def test_test_func(self):
        Order.objects.get(pk=self.order.id).delete()
        response = self.client.get(self.url)

        assert response.status_code == 302

    def test_response_and_context(self):
        orderitem_with_products_qs = list(
            OrderItem.objects.filter(order=self.order.id).select_related("product")
        )
        order_cost = 0
        for orderitem in orderitem_with_products_qs:
            order_cost += orderitem.product.price * orderitem.quantity
        producers_query = Producer.objects.filter(is_active=True).values("slug", "name")
        producers = [
            [producer["slug"], producer["name"]] for producer in producers_query
        ]

        producer = Producer.objects.get(pk=self.producer.id)
        products_with_related = (
            Product.objects.filter(producer=producer.id)
            .filter(is_active=True)
            .prefetch_related("weight_schemes", "statuses")
        )
        products_with_available_quantity = calculate_available_quantity(
            products_with_related
        )

        response = self.client.get(self.url)
        context_data = response.context

        logger.info(context_data["form"])

        assert response.status_code == 200
        assert context_data["order"] == self.order
        assert list(context_data["orderitems"]) == orderitem_with_products_qs
        assert context_data["order_cost"] == order_cost != 0
        assert list(context_data["producers"]) == producers
        assert context_data["producer"] == producer
        assert list(context_data["products"]) == list(products_with_available_quantity)

    def test_create(self):
        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": self.product1.id,
            "form-0-quantity": "1.000",
        }

        pre_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)

        logger.info(messages)

        assert response.status_code == 200
        assert pre_create_orderitem_count + 1 == post_create_orderitem_count
        assert f"{self.product1.name}: Produkt został dodany do zamówienia." in messages

    def test_max_quantity_validation(self):
        for _ in range(2):
            OrderItemFactory(product=self.product1, quantity=5, order=OrderFactory())

        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": self.product1.id,
            "form-0-quantity": "1.000",
        }

        pre_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert pre_create_orderitem_count == post_create_orderitem_count
        assert response.status_code == 200
        assert (
            f"{self.product1}: Przekroczona maksymalna ilość lub waga zamawianego produktu. Nie ma tyle."
            in messages
        )

    def test_product_already_in_order_validation(self):
        OrderItemFactory(product=self.product1, order=self.order)

        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": self.product1.id,
            "form-0-quantity": "1.000",
        }

        pre_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert (
            f"{self.product1.name}: Dodałeś już ten produkt do zamówienia." in messages
        )
        assert pre_create_orderitem_count == post_create_orderitem_count
        assert response.status_code == 200

    def test_order_deadline_validation(self):
        product2 = ProductFactory(
            weight_schemes=self.weight_scheme_list,
            order_deadline=datetime.datetime(2023, 9, 17, 18).astimezone(),
        )
        OrderItemFactory(product=product2, quantity=9, order=OrderFactory())

        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": product2.id,
            "form-0-quantity": "0.500",
        }

        pre_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert pre_create_orderitem_count == post_create_orderitem_count
        assert response.status_code == 200
        assert (
            f"{product2.name}: Termin minął, nie możesz już dodać tego produktu do zamówienia."
            in messages
        )


@pytest.mark.django_db
class TestOrderCreateView(TestCase):
    def setUp(self):
        self.producer = ProducerFactory()
        self.url = reverse("order-create")
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_order_exists_validation(self):
        order = OrderFactory(user=self.user)
        order = Order.objects.get(pk=order.id)
        order.date_created = timezone.now()

        form_data = {
            "pick_up_day": "środa",
        }

        pre_save_order_count = Order.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_save_order_count = Order.objects.count()

        messages = list_messages(response)
        assert "Masz już zamówienie na ten tydzień." in messages
        assert pre_save_order_count == post_save_order_count
        assert response.status_code == 200

    def test_order_create_view(self):
        form_data = {
            "pick_up_day": "środa",
        }

        pre_save_order_count = Order.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_save_order_count = Order.objects.count()

        messages = list_messages(response)
        assert "Zamówienie zostało utworzone. Dodaj produkty." in messages
        assert pre_save_order_count + 1 == post_save_order_count
        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderUpdateView(TestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.user = self.profile.user
        self.client.force_login(self.user)
        self.order = OrderFactory(user=self.user, pick_up_day="środa")
        for _ in range(0, 5):
            OrderItemFactory(order=self.order)

    def test_update_view(self):
        form_data = {
            "pick_up_day": "czwartek",
        }
        url = reverse("order-update", kwargs={"pk": self.order.id})
        response = self.client.post(url, data=form_data, follow=True)
        order_db = Order.objects.get(id=self.order.id)

        messages = list_messages(response)
        assert "Dzień odbioru zamówienia został zmieniony." in messages
        assert order_db.pick_up_day == "czwartek"
        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderDeleteView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.order = OrderFactory(user=self.user, pick_up_day="środa")
        for _ in range(0, 5):
            OrderItemFactory(order=self.order)

    def test_delete_view(self):
        order_count = Order.objects.count()
        orderitem_count = OrderItem.objects.count()
        url = reverse("order-delete", kwargs={"pk": self.order.id})
        response = self.client.delete(url)
        order_count_post_del = Order.objects.count()
        orderitem_count_post_del = OrderItem.objects.count()

        assert order_count == 1
        assert order_count_post_del == 0
        assert orderitem_count == 5
        assert orderitem_count_post_del == 0
        assert response.status_code == 302

    def test_delete_nonexistent_order(self):
        pk = 9999
        url = reverse("order-delete", kwargs={"pk": pk})
        response = self.client.delete(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestProducerBoxReportView(TestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.client.force_login(self.user)
        self.url = reverse("producer-box-report")
        for _ in range(0, 5):
            ProductFactory()
        self.orderitem1 = OrderItemFactory(
            product=ProductFactory(name="Alaska"), quantity=4
        )
        self.orderitem2 = OrderItemFactory(
            product=ProductFactory(name="Barabasz"), quantity=1
        )
        self.orderitem3 = OrderItemFactory(
            product=ProductFactory(name="Celuloza"), quantity=2
        )

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        products = Product.objects.filter(orderitems__isnull=False)

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
        self.user_list = []
        for i in range(5):
            profile = ProfileFactory(koop_id=i)
            OrderFactory(user=profile.user)
            self.user_list.append(profile.user)

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        assert len(self.user_list) == len(context_data['users'])
        assert response.status_code == 200
        for user in context_data['users']:
            assert user in self.user_list


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
