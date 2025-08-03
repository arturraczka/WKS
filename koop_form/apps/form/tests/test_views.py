import random
from decimal import Decimal

import django.contrib.staticfiles.storage
import pytest
import datetime
import logging

from django.urls import reverse
from django.test import TestCase
from django.utils import timezone
from django.conf import settings

from apps.form.models import Order, OrderItem, Producer, Product
from apps.user.models import UserProfileFund
from apps.form.services import (
    list_messages,
)
from factories.model_factories import (
    ProducerFactory,
    UserFactory,
    WeightSchemeFactory,
    ProductFactory,
    OrderItemFactory,
    OrderFactory,
    ProfileFactory,
    UserProfileFundFactory,
)

logger = logging.getLogger("django.server")


@pytest.fixture()
def producers():
    ProducerFactory(name="Karol Jung", slug="karol-jung")
    ProducerFactory(name="Adam Pritz", slug="adam-pritz")
    for _ in range(
        0,
        3,
    ):
        ProducerFactory(is_active=False)


def factor_producers():
    ProducerFactory(name="Karol Jung", slug="karol-jung")
    ProducerFactory(name="Adam Pritz", slug="adam-pritz")
    for _ in range(
        0,
        3,
    ):
        ProducerFactory(is_active=False)


producers_list = [["adam-pritz", "Adam Pritz"], ["karol-jung", "Karol Jung"]]


@pytest.mark.usefixtures("producers")
@pytest.mark.django_db
class TestProductsView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.producer_used = Producer.objects.get(name="Karol Jung")
        self.producer_dummy = Producer.objects.get(name="Adam Pritz")
        for _ in range(0, 5):
            ProductFactory(producer=self.producer_used)
            ProductFactory(producer=self.producer_dummy)
        self.url = reverse("products", kwargs={"slug": self.producer_used.slug})

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        products = list(
            Product.objects.filter(producer=self.producer_used.id)
            .filter(is_active=True)
            .prefetch_related("weight_schemes", "statuses")
        )

        assert response.status_code == 200
        assert context_data["producer"] == self.producer_used
        assert list(context_data["products"]) == products
        assert sorted(list(context_data["producers"])) == producers_list


#this test is probably incorrect because order producers does not work, order_producers.html is in archive and maybe it this test and whole order_produers view should be deleted
#TODO get confirmation from Artur
# @pytest.mark.django_db
# class TestOrderProducersView(TestCase):
#     def setUp(self):
#         self.user = UserFactory()
#         self.client.force_login(self.user)
#         factor_producers()
#         self.producer1 = Producer.objects.get(name="Karol Jung")
#         self.producer2 = Producer.objects.get(name="Adam Pritz")
#         self.order = OrderFactory(user=self.user)
#         self.url = reverse("order-producers")
#
#     def test_response_and_context(self):
#         response = self.client.get(self.url)
#         context_data = response.context
#
#         assert response.status_code == 200
#         assert sorted(list(context_data["producers"])) == producers_list
#
#     def test_test_func(self):
#         Order.objects.get(pk=self.order.id).delete()
#         response = self.client.get(self.url)
#
#         assert response.status_code == 302


@pytest.mark.django_db
class TestOrderProductsFormView(TestCase):
    def setUp(self):
        factor_producers()
        #TODO fix in future - refactor whole DEBUG dependency in app tests are always run with DEBUG=false https://docs.djangoproject.com/en/5.0/topics/testing/overview/#other-test-conditions
        settings.DEBUG=True
        self.producer1 = Producer.objects.get(name="Karol Jung")
        self.producer2 = Producer.objects.get(name="Adam Pritz")
        self.url = reverse("order-products-form", kwargs={"slug": self.producer1.slug})
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.weight_scheme_list = [
            WeightSchemeFactory(quantity=val)
            for val in [ 0.500, 1.000, 2.000, 3.000, 4.000, 5.000]
        ]
        self.product0 = ProductFactory(
            name="agawa",
            producer=self.producer1,
            weight_schemes=self.weight_scheme_list,
            order_max_quantity=None,
            quantity_in_stock=Decimal("6.5"),
            price=12,
            description="test description 0",
        )
        self.product1 = ProductFactory(
            name="aronia",
            producer=self.producer1,
            weight_schemes=self.weight_scheme_list,
            order_max_quantity=Decimal("9.7"),
            price=3.5,
            description="test description 1",
        )
        self.product2 = ProductFactory(
            name="burak",
            producer=self.producer2,
            weight_schemes=self.weight_scheme_list,
            quantity_in_stock=Decimal("6.5"),
            price=6,
        )
        for _ in range(0, 3):
            ProductFactory(producer=self.producer1, is_active=False)
        self.order1 = OrderFactory(user=self.user)
        self.order2 = OrderFactory()
        self.orderitem1 = OrderItemFactory(
            product=self.product1, order=self.order1, quantity=Decimal(0.5)
        )
        self.orderitem2 = OrderItemFactory(
            product=self.product2, order=self.order1, quantity=Decimal(3.0)
        )
        self.orderitem3 = OrderItemFactory(product=self.product1, quantity=1)
        self.orderitem4 = OrderItemFactory(product=self.product1)
        number = random.randint(8, 20)
        past_date = timezone.now() - datetime.timedelta(days=number)
        item = OrderItem.objects.get(id=self.orderitem4.id)
        item.item_ordered_date = past_date
        item.save()

    def tearDown(self):
        # TODO fix in future - refactor whole DEBUG dependency in app tests are always run with DEBUG=false https://docs.djangoproject.com/en/5.0/topics/testing/overview/#other-test-conditions
        settings.DEBUG = False

    def test_test_func(self):
        Order.objects.get(pk=self.order1.id).delete()
        response = self.client.get(self.url)

        assert response.status_code == 302

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context_data = response.context

        assert list(context_data["orderitems"]) == [self.orderitem1, self.orderitem2]
        assert context_data["order_cost"] == Decimal(19.75)
        assert list(context_data["order"].products.all()) == [self.product1, self.product2]
        #TODO fix ? ask Artur
        # assert context_data["products_description"] == [
        #     "test description 1",
        #     "test description 2",
        # ]
        # assert context_data["available_quantities_list"] == [
        #     Decimal("6.500"),
        #     Decimal("8.200"),
        # ]
        assert response.status_code == 200
        assert context_data["order"] == self.order1
        assert sorted(list(context_data["producers"])) == producers_list
        assert context_data["producer"] == self.producer1

    def test_create(self):
        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": self.product0.id,
            "form-0-order": self.order1.id,
            "form-0-quantity": "1.000",
        }

        pre_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)

        logger.info(messages)

        assert response.status_code == 200
        assert pre_create_orderitem_count + 1 == post_create_orderitem_count
        assert f"{self.product0.name}: Produkt został dodany do zamówienia." in messages

    def test_max_quantity_validation(self):
        #given
        for _ in range(2):
            form_data = {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 0,
                "form-0-product": self.product0.id,
                "form-0-order": OrderFactory().id,
                "form-0-quantity": "3.000",
            }
            response = self.client.post(self.url, data=form_data, follow=True)
            messages = list_messages(response)
            print(messages)

        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": self.product0.id,
            "form-0-order": self.order1.id,
            "form-0-quantity": "1.000",
        }
        pre_create_orderitem_count = OrderItem.objects.count()

        #when
        response = self.client.post(self.url, data=form_data, follow=True)

        #then
        post_create_orderitem_count = OrderItem.objects.count()
        messages = list_messages(response)
        assert pre_create_orderitem_count == post_create_orderitem_count
        assert response.status_code == 200
        assert (
            f"{self.product0.name}: Przekroczona maksymalna ilość lub waga zamawianego produktu. Nie ma tyle."
            in messages
        )

    def test_product_already_in_order_validation(self):
        OrderItemFactory(product=self.product0, order=self.order1)

        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": self.product0.id,
            "form-0-order": self.order1.id,
            "form-0-quantity": "1.000",
        }

        pre_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert (
            f"{self.product0.name}: Dodałeś już ten produkt do zamówienia." in messages
        )
        assert pre_create_orderitem_count == post_create_orderitem_count
        assert response.status_code == 200

    def test_order_deadline_validation(self):
        self.product0.order_deadline = datetime.datetime(2023, 9, 17, 18).astimezone()
        self.product0.save()

        form_data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-product": self.product0.id,
            "form-0-order": self.order1.id,
            "form-0-quantity": "1.000",
        }

        pre_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        post_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert pre_create_orderitem_count == post_create_orderitem_count
        assert response.status_code == 200
        assert (
            f"{self.product0.name}: Termin minął, nie możesz już dodać tego produktu do zamówienia."
            in messages
        )


@pytest.mark.django_db
class TestOrderCreateView(TestCase):
    def setUp(self):
        #TODO fix in future - refactor whole DEBUG dependency in app tests are always run with DEBUG=false https://docs.djangoproject.com/en/5.0/topics/testing/overview/#other-test-conditions
        settings.DEBUG=True
        self.producer = ProducerFactory()
        self.url = reverse("order-create")
        self.user = UserFactory()
        self.client.force_login(self.user)

    def tearDown(self):
        #TODO fix in future - refactor whole DEBUG dependency in app tests are always run with DEBUG=false https://docs.djangoproject.com/en/5.0/topics/testing/overview/#other-test-conditions
        settings.DEBUG=False

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
class TestOrderUpdateFormView(TestCase):
    def setUp(self):
        factor_producers()
        self.producer1 = Producer.objects.get(name="Karol Jung")
        self.producer2 = Producer.objects.get(name="Adam Pritz")

        self.url = reverse("order-update-form")
        self.user = UserFactory()
        fund = UserProfileFund.objects.get(value=Decimal("1.1"))
        self.profile = ProfileFactory(user=self.user, fund=fund)
        self.client.force_login(self.user)

        self.order1 = OrderFactory(user=self.user)
        self.order2 = OrderFactory(user=self.user)
        self.order3 = OrderFactory()
        number = random.randint(8, 20)
        past_date = timezone.now() - datetime.timedelta(days=number)
        order = Order.objects.get(id=self.order2.id)
        order.date_created = past_date
        order.save()

        self.product0 = ProductFactory(name="alfa", price=Decimal("6.5"))
        self.product1 = ProductFactory(name="beta", price=Decimal("5"))
        self.product2 = ProductFactory(name="gamma", price=Decimal("12.8"))
        ProductFactory(), ProductFactory()

        self.orderitem1 = OrderItemFactory(
            product=self.product0, order=self.order1, quantity=Decimal(0.5)
        )
        self.orderitem2 = OrderItemFactory(
            product=self.product1, order=self.order1, quantity=3
        )
        self.orderitem3 = OrderItemFactory(
            product=self.product1, order=self.order2, quantity=7
        )
        self.orderitem4 = OrderItemFactory(product=self.product1)

    def test_response_and_context(self):
        response = self.client.get(self.url)
        context = response.context

        assert response.status_code == 200
        assert context["order"] == self.order1
        assert context["fund"] == Decimal("1.1")
        assert list(context["orderitems"]) == [self.orderitem1, self.orderitem2]
        assert context["order_cost"] == Decimal("18.25")
        assert context["order_cost_with_fund"] == Decimal("20.075")
        assert list(context["products"]) == [self.product0, self.product1]


@pytest.mark.django_db
class TestOrderUpdateView(TestCase):
    def setUp(self):
        fund = UserProfileFund.objects.get(value=Decimal("1.1"))
        self.profile = ProfileFactory(fund=fund)
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
