from decimal import Decimal

import pytest
import logging

from django.conf import settings
from django.test import TestCase

from apps.form.models import Order, WeightScheme, product_weight_schemes
from apps.form.services import calculate_order_number
from apps.user.models import UserProfileFund
from factories.model_factories import (
    UserFactory,
    ProductFactory,
    OrderItemFactory,
    OrderFactory,
    ProducerFactory,
    WeightSchemeFactory,
    ProfileFactory,
)

logger = logging.getLogger("django.server")

pytestmark = pytest.mark.django_db


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


class TestProduct(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.order = OrderFactory(
            user=self.user, order_number=calculate_order_number(Order)
        )
        self.order_second = OrderFactory(
            user=self.user, order_number=calculate_order_number(Order)
        )
        self.product = ProductFactory(order_max_quantity=100)

    def test_order_ordering(self):
        self.assertEquals(self.order.order_number, 1)
        self.assertEquals(self.order_second.order_number, 2)

    def test_signal_add_zero_as_weight_scheme(self):
        # given
        zero_weight_scheme = WeightScheme.objects.get(quantity=0)
        # when then
        assert zero_weight_scheme in self.product.weight_schemes.all()


class Test_product_weight_schemes(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.order = OrderFactory(
            user=self.user, order_number=calculate_order_number(Order)
        )
        self.order_second = OrderFactory(
            user=self.user, order_number=calculate_order_number(Order)
        )
        self.product = ProductFactory(order_max_quantity=100)
        self.weight_scheme_1 = WeightSchemeFactory(quantity=1)
        self.weight_scheme_2 = WeightSchemeFactory(quantity=2)

    def test_save_prevent_update_zero_as_weight_scheme(self):
        # given
        zero_weight_scheme = WeightScheme.objects.get(quantity=0)
        product_weight_schemes_0 = product_weight_schemes.objects.get(
            weightscheme_id=zero_weight_scheme.id
        )

        # when
        product_weight_schemes_0.weightscheme = self.weight_scheme_1
        product_weight_schemes_0.save()

        #  then
        self.assertTrue(zero_weight_scheme in self.product.weight_schemes.all())

    def test_save_update_weight_scheme(self):
        # given
        self.product.weight_schemes.add(self.weight_scheme_1)
        product_weight_schemes_1 = product_weight_schemes.objects.get(
            weightscheme_id=self.weight_scheme_1.id
        )

        # when
        product_weight_schemes_1.weightscheme = self.weight_scheme_2
        product_weight_schemes_1.save()

        # then
        self.assertFalse(self.weight_scheme_1 in self.product.weight_schemes.all())
        self.assertTrue(self.weight_scheme_2 in self.product.weight_schemes.all())


class TestProducerModel(TestCase):
    def setUp(self):
        self.producer = ProducerFactory(name="Wielka! Korba p.13")

        for _ in range(0, 5):
            product = ProductFactory(producer=self.producer)
            for _ in range(0, 3):
                OrderItemFactory(product=product)

    def test_slug_creation(self):
        assert self.producer.slug == "wielka-korba-p13"


class TestOrderItem:
    def test_item_cost(self):
        item = OrderItemFactory()
        assert item.item_cost == item.product.price * item.quantity


class TestOrder:
    @pytest.fixture(autouse=True)
    def _setup(self, bare_order):
        self.product_1 = ProductFactory()
        self.product_2 = ProductFactory()
        self.item_1 = OrderItemFactory(
            product=self.product_1, order=bare_order, quantity=2.5
        )
        self.item_2 = OrderItemFactory(
            product=self.product_2, order=bare_order, quantity=4
        )
        self.fund = UserProfileFund.objects.first()
        self.profile = ProfileFactory(user=bare_order.user, fund=self.fund)
        self.expected_cost = (
            self.product_1.price * self.item_1.quantity
            + +self.product_2.price * self.item_2.quantity
        )
        self.expected_cost_with_fund = (
            Decimal(self.expected_cost) * self.profile.fund.value
        )
        self.paid = 100
        bare_order.paid_amount = self.paid
        bare_order.save(update_fields=["paid_amount"])

    def test_user_fund_when_user_has_no_profile(self, bare_order):
        bare_order.user.userprofile = None
        bare_order.user.save()
        assert bare_order.user_fund == settings.DEFAULT_USER_FUND

    def test_user_fund(self, bare_order):
        assert bare_order.user_fund == self.profile.fund.value

    def test_order_cost(self, bare_order):
        assert bare_order.order_cost == self.expected_cost

    def test_order_cost_unsaved_order(self):
        order = OrderFactory.build()
        assert order.order_cost == 0

    def test_order_cost_no_items(self):
        order = OrderFactory.build()
        assert order.order_cost == 0

    def test_order_cost_with_fund(self, bare_order):
        assert bare_order.order_cost_with_fund == self.expected_cost_with_fund

    def test_order_cost_with_fund_snapshot(self, bare_order):
        fund_snapshot_value = Decimal("1.2")
        bare_order.fund_snapshot = fund_snapshot_value
        bare_order.save(update_fields=["fund_snapshot"])
        assert (
            bare_order.order_cost_with_fund
            == Decimal(self.expected_cost) * fund_snapshot_value
        )

    def test_get_paid_amount_no_paid_amount(self, bare_order):
        bare_order.paid_amount = None
        bare_order.save()
        assert bare_order.get_paid_amount() == 0

    def test_get_paid_amount(self, bare_order):
        assert bare_order.get_paid_amount() == self.paid

    def test_order_balance(self, bare_order):
        assert bare_order.order_balance == self.paid - self.expected_cost_with_fund
