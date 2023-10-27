import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
import datetime
from apps.form.models import Order, OrderItem, Producer, Product
from apps.form.services import list_messages
from apps.form.tests.factories import (
    ProducerFactory,
    UserFactory,
    WeightSchemeFactory,
    ProductFactory,
    OrderWithProductFactory,
    OrderItemFactory,
    OrderFactory,
)
from django.test import TestCase


@pytest.mark.django_db
class TestProducerListView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.producer1 = ProducerFactory()
        self.producer2 = ProducerFactory()
        self.url = reverse("producer-list")

    def test_get(self):
        response = self.client.get(self.url)
        context_data = response.context
        producers = list(Producer.objects.all())

        assert response.status_code == 200
        assert list(context_data["producers"]) == producers


@pytest.mark.django_db
class TestProducerWithProductsDetailView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.weight_scheme_zero = WeightSchemeFactory(quantity=0)
        self.product = ProductFactory()
        self.url = reverse(
            "producer-products-detail", kwargs={"slug": self.product.producer.slug}
        )

    def test_get(self):
        response = self.client.get(self.url)
        context_data = response.context

        products_with_related = list(
            Product.objects.filter(producer=self.product.producer.id).prefetch_related(
                "weight_schemes", "statuses"
            )
        )
        producer = Producer.objects.get(pk=self.product.producer.id)
        producers = list(Producer.objects.all())

        assert response.status_code == 200
        assert context_data["producer"] == producer
        assert list(context_data["products_with_related"]) == products_with_related
        assert list(context_data["producers"]) == producers


@pytest.mark.django_db
class TestFormProducerListView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.producer = ProducerFactory()
        self.client.force_login(self.user)
        self.order = OrderFactory(user=self.user)

    def test_get_update_view(self):
        url = reverse("form-producer-list")
        response = self.client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderItemListCreateProductListView(TestCase):
    def setUp(self):
        self.producer = ProducerFactory()
        self.url = reverse("orderitem-create", kwargs={"slug": self.producer.slug})
        self.user = UserFactory()
        self.client.force_login(self.user)
        weight_scheme1 = WeightSchemeFactory(quantity=0.5)
        weight_scheme2 = WeightSchemeFactory(quantity=0.2)
        weight_scheme3 = WeightSchemeFactory(quantity=8)
        weight_scheme4 = WeightSchemeFactory(quantity=2)
        weight_scheme0 = WeightSchemeFactory(quantity=0)
        self.weight_scheme_list = [
            weight_scheme1,
            weight_scheme2,
            weight_scheme3,
            weight_scheme4,
        ]
        self.product1 = ProductFactory(producer=self.producer)
        self.order = OrderWithProductFactory(user=self.user)
        self.order2 = OrderWithProductFactory()
        self.orderitem = OrderItemFactory(
            product=self.product1, quantity=5, order=self.order
        )

    def test_get(self):
        orderitem_with_products_qs = list(
            OrderItem.objects.filter(order=self.order.id).select_related("product")
        )
        order_cost = 0
        for orderitem in orderitem_with_products_qs:
            order_cost += orderitem.product.price * orderitem.quantity
        producers = list(Producer.objects.all())
        producer = Producer.objects.get(pk=self.producer.id)
        products_with_related = list(
            Product.objects.filter(producer=producer.id).prefetch_related(
                "weight_schemes", "statuses"
            )
        )

        response = self.client.get(self.url)
        context_data = response.context

        assert response.status_code == 200
        assert context_data["order"] == self.order
        assert list(context_data["orderitems"]) == orderitem_with_products_qs
        assert context_data["order_cost"] == order_cost != 0
        assert list(context_data["producers"]) == producers
        assert context_data["producer"] == producer
        assert list(context_data["products_with_related"]) == products_with_related

    def test_create(self):
        product2 = ProductFactory(
            producer=self.producer,
            order_max_quantity=10,
            weight_schemes=self.weight_scheme_list,
        )
        OrderItemFactory(product=product2, quantity=9, order=self.order2)
        form_data = {
            "product": product2.id,
            "quantity": 0.5,
        }

        before_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        after_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert "Produkt został dodany do zamówienia." in messages
        assert before_create_orderitem_count + 1 == after_create_orderitem_count
        assert response.status_code == 200

    def test_max_quantity_validation(self):
        quantity_already = 2
        quantity_posted = 8
        max_quantity = 5
        product2 = ProductFactory(
            order_max_quantity=max_quantity, weight_schemes=self.weight_scheme_list
        )
        OrderItemFactory(product=product2, quantity=quantity_already, order=self.order2)
        form_data = {
            "product": product2.id,
            "quantity": quantity_posted,
        }

        before_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        after_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert (
            "Przekroczona maksymalna ilość zamawianego produktu. Nie ma tyle."
            in messages
        )
        assert before_create_orderitem_count == after_create_orderitem_count
        assert response.status_code == 200

    def test_product_already_in_order_validation(self):
        product2 = ProductFactory(weight_schemes=self.weight_scheme_list)
        OrderItemFactory(product=product2, order=self.order)
        form_data = {
            "product": product2.id,
            "quantity": 0.5,
        }

        before_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        after_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert "Dodałeś już ten produkt do zamówienia." in messages
        assert before_create_orderitem_count == after_create_orderitem_count
        assert response.status_code == 200

    def test_weight_scheme_validation(self):
        test_weight_scheme = WeightSchemeFactory(quantity=1)
        product2 = ProductFactory(weight_schemes=[test_weight_scheme])

        form_data = {
            "product": product2.id,
            "quantity": 0.7,
        }

        before_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        after_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert (
            "Nieprawidłowa waga zamawianego produtku. Wybierz wagę z dostępnego schematu."
            in messages
        )
        assert before_create_orderitem_count == after_create_orderitem_count
        assert response.status_code == 200

    def test_order_deadline_validation(self):
        product2 = ProductFactory(
            weight_schemes=self.weight_scheme_list,
            order_deadline=datetime.datetime(2023, 9, 17, 18),
        )
        OrderItemFactory(product=product2, quantity=9, order=self.order2)
        form_data = {
            "product": product2.id,
            "quantity": 0.5,
        }

        before_create_orderitem_count = OrderItem.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        after_create_orderitem_count = OrderItem.objects.count()

        messages = list_messages(response)
        assert (
            "Termin minął, nie możesz już dodać tego produktu do zamówienia."
            in messages
        )
        assert before_create_orderitem_count == after_create_orderitem_count
        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderCreateView(TestCase):
    def setUp(self):
        self.producer = ProducerFactory()
        self.url = reverse("order-create")
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_get(self):
        response = self.client.get(self.url)

        assert response.status_code == 200

    def test_order_exists_validation(self):
        order = OrderFactory(user=self.user)
        order = Order.objects.get(pk=order.id)
        order.date_created = datetime.datetime.now()

        form_data = {
            "pick_up_day": "środa",
        }

        before_post_order_count = Order.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        after_post_order_count = Order.objects.count()

        messages = list_messages(response)
        assert "Masz już zamówienie na ten tydzień." in messages
        assert before_post_order_count == after_post_order_count
        assert response.status_code == 200

    def test_order_create_view(self):
        form_data = {
            "pick_up_day": "środa",
        }

        before_post_order_count = Order.objects.count()
        response = self.client.post(self.url, data=form_data, follow=True)
        after_post_order_count = Order.objects.count()

        messages = list_messages(response)
        assert "Zamówienie zostało utworzone. Dodaj produkty." in messages
        assert before_post_order_count + 1 == after_post_order_count
        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderDetailOrderItemListView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse("order-detail")

    def test_test_mixin(self):
        response = self.client.get(self.url)
        assert response.status_code == 403

    def test_get(self):
        order = OrderFactory(user=self.user)
        OrderItemFactory(order=order)
        OrderItemFactory(order=order)
        orderitem_with_products = list(
            OrderItem.objects.filter(order=order.id).select_related("product")
        )
        order_cost = 0
        for orderitem in orderitem_with_products:
            order_cost += orderitem.product.price * orderitem.quantity

        response = self.client.get(self.url)
        context_data = response.context

        assert response.status_code == 200
        assert context_data["order"] == order
        assert list(context_data["orderitems"]) == orderitem_with_products
        assert context_data["order_cost"] == order_cost


@pytest.mark.django_db
class TestGetOrderUpdateOrderDeleteViews(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.order = OrderFactory(user=self.user)

    def test_get_update_view(self):
        url = reverse("order-update", kwargs={"pk": self.order.id})
        response = self.client.get(url)

        assert response.status_code == 200

    def test_get_delete_view(self):
        url = reverse("order-delete", kwargs={"pk": self.order.id})
        response = self.client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestGetOrderItemUpdateOrderItemDeleteViews(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.order = OrderFactory(user=self.user)
        self.orderitem = OrderItemFactory(order=self.order)

    def test_get_update_view(self):
        url = reverse("orderitem-update", kwargs={"pk": self.orderitem.id})
        response = self.client.get(url)

        assert response.status_code == 200

    def test_get_delete_view(self):
        url = reverse("orderitem-delete", kwargs={"pk": self.orderitem.id})
        response = self.client.get(url)

        assert response.status_code == 200
