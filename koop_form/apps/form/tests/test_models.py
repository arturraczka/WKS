import pytest
import logging

from django.test import TestCase

from apps.form.models import Order, WeightScheme, product_weight_schemes
from apps.form.services import calculate_order_number
from factories.model_factories import (
    UserFactory,
    ProductFactory,
    OrderItemFactory,
    OrderFactory,
    ProducerFactory, WeightSchemeFactory,
)

logger = logging.getLogger("django.server")


@pytest.mark.django_db
class TestWeightScheme:
    def test_signal_init_weight_scheme_with_zero(self):
        assert WeightScheme.objects.filter(quantity=0).exists()

    def test_delete(self):
        weight_scheme_zero = WeightScheme.objects.get(quantity=0)
        weight_scheme_1 = WeightScheme.objects.create(quantity=1)
        weight_scheme_zero.delete()
        weight_scheme_1.delete()
        assert WeightScheme.objects.filter(quantity=0).exists()
        assert not WeightScheme.objects.filter(quantity=1).exists()


@pytest.mark.django_db
class TestProduct(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.order = OrderFactory(user=self.user, order_number=calculate_order_number(Order))
        self.order_second = OrderFactory(user=self.user, order_number=calculate_order_number(Order))
        self.product = ProductFactory(order_max_quantity=100)

    def test_order_ordering(self):
        self.assertEquals(self.order.order_number, 1)
        self.assertEquals(self.order_second.order_number, 2)

    def test_signal_add_zero_as_weight_scheme(self):
        #given
        zero_weight_scheme = WeightScheme.objects.get(quantity=0)
        #when then
        assert zero_weight_scheme in self.product.weight_schemes.all()

@pytest.mark.django_db
class Test_product_weight_schemes(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.order = OrderFactory(user=self.user, order_number=calculate_order_number(Order))
        self.order_second = OrderFactory(user=self.user, order_number=calculate_order_number(Order))
        self.product = ProductFactory(order_max_quantity=100)
        self.weight_scheme_1 = WeightSchemeFactory(quantity=1)
        self.weight_scheme_2 = WeightSchemeFactory(quantity=2)

    def test_save_prevent_update_zero_as_weight_scheme(self):
        # given
        zero_weight_scheme = WeightScheme.objects.get(quantity=0)
        product_weight_schemes_0 = product_weight_schemes.objects.get(weightscheme_id=zero_weight_scheme.id)

        # when
        product_weight_schemes_0.weightscheme = self.weight_scheme_1
        product_weight_schemes_0.save()

        #  then
        self.assertTrue(zero_weight_scheme in self.product.weight_schemes.all())

    def test_save_update_weight_scheme(self):
        # given
        self.product.weight_schemes.add(self.weight_scheme_1)
        product_weight_schemes_1 = product_weight_schemes.objects.get(weightscheme_id=self.weight_scheme_1.id)

        # when
        product_weight_schemes_1.weightscheme = self.weight_scheme_2
        product_weight_schemes_1.save()

        # then
        self.assertFalse(self.weight_scheme_1 in self.product.weight_schemes.all())
        self.assertTrue(self.weight_scheme_2 in self.product.weight_schemes.all())


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
