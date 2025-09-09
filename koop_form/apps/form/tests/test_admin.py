from decimal import Decimal
import pytest
from unittest.mock import patch

from django.contrib import messages
from django.contrib.admin.options import ModelAdmin as DjangoModelAdmin

from apps.form.admin import OrderAdmin, OrderItemAdmin
from apps.form.models import Order, Product, OrderItem
from apps.form.services import display_as_zloty
from factories.model_factories import OrderFactory, OrderItemFactory, ProductFactory

pytestmark = pytest.mark.django_db


class TestOrderAdmin:
    @pytest.fixture(autouse=True)
    def _setup(self, admin_user, request_factory, admin_site):
        self.model_admin = OrderAdmin(Order, admin_site)
        self.request = request_factory.post("")
        self.request.user = admin_user

    def test_user_balance_method(self, user, user_profile, order):
        assert self.model_admin.user_balance(
            order
        ) == f"{order.user_balance:.1f} zł".replace(".", ",")

    def test_order_cost_with_fund_method(self, user, user_profile, order):
        assert self.model_admin.order_cost_with_fund(
            order
        ) == f"{order.order_cost_with_fund:.1f} zł".replace(".", ",")

    def test_save_model_assigns_order_number(self, user):
        OrderFactory()
        OrderFactory()
        order = OrderFactory.build(order_number=None, user=user)
        order.paid_amount = None
        self.model_admin.save_model(self.request, order, form=None, change=False)

        order.refresh_from_db()
        expected_order_number = 3
        assert order.order_number == expected_order_number

    def test_update_user_balance_db_paid_equals_new_paid(
        self, user, user_profile, order
    ):
        old_balance = user_profile.payment_balance
        old_paid = order.paid_amount
        new_paid = old_paid
        order.paid_amount = new_paid
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert user_profile.payment_balance == old_balance

    def test_update_user_balance_new_paid(self, user, user_profile, order):
        old_balance = user_profile.payment_balance
        old_paid = order.paid_amount
        new_paid = Decimal("50")
        paid_delta = new_paid - old_paid
        order.paid_amount = new_paid
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert order.paid_amount == new_paid
        assert user_profile.payment_balance == old_balance + paid_delta

    def test_update_user_balance_old_paid_is_none(self, user, user_profile, order):
        old_balance = user_profile.payment_balance
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        new_paid = Decimal("50")
        order.paid_amount = new_paid
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert user_profile.payment_balance == order.order_balance + old_balance

    def test_update_user_balance_new_paid_is_none(self, user, user_profile, order):
        old_paid = order.paid_amount
        old_balance = user_profile.payment_balance
        order.paid_amount = None
        self.model_admin.save_model(self.request, order, form=None, change=True)
        order.refresh_from_db()
        user_profile.refresh_from_db()

        assert (
            user_profile.payment_balance
            == old_balance - old_paid + order.order_cost_with_fund
        )

    def test_is_settled__paid(self, order):
        assert order.paid_amount is not None
        assert self.model_admin.is_settled(order) == "Tak"

    def test_is_settled__paid_0(self, order):
        order.paid_amount = 0
        order.save(update_fields=["paid_amount"])
        assert self.model_admin.is_settled(order) == "Tak"

    def test_is_settled__not_paid(self, order):
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        assert self.model_admin.is_settled(order) == "-"

    def test_user_fund(self, order):
        assert order.user_fund is not None
        assert self.model_admin.user_fund(order) == order.user_fund

    def test_order_cost(self, order):
        assert order.order_cost is not None
        assert self.model_admin.order_cost(order) == display_as_zloty(order.order_cost)

    def test_user_and_order_balance__not_paid(self, order, user_profile):
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        assert order.order_balance is not None
        assert order.user_balance is not None
        assert self.model_admin.user_and_order_balance(order) == display_as_zloty(
            -order.order_balance - order.user_balance
        )

    def test_user_and_order_balance__paid(self, order, user_profile):
        assert order.paid_amount is not None
        assert self.model_admin.user_and_order_balance(order) == display_as_zloty(
            -order.user_balance
        )

    def test_delete_model(self, bare_order, rf):
        product_1 = ProductFactory()
        item_1 = OrderItemFactory(order=bare_order, product=product_1)
        product_2 = ProductFactory()
        item_2 = OrderItemFactory(order=bare_order, product=product_2)
        self.model_admin.delete_model(rf.get("/"), bare_order)
        assert not Order.objects.filter(id=bare_order.id).exists()
        product_1_db = Product.objects.get(id=product_1.id)
        product_2_db = Product.objects.get(id=product_2.id)
        assert (
            product_1_db.quantity_in_stock
            == product_1.quantity_in_stock + item_1.quantity
        )
        assert (
            product_2_db.quantity_in_stock
            == product_2.quantity_in_stock + item_2.quantity
        )

    def test_delete_queryset(self, rf):
        order_1 = OrderFactory()
        order_2 = OrderFactory()
        product = ProductFactory()
        item_1 = OrderItemFactory(order=order_1, product=product)
        item_2 = OrderItemFactory(order=order_2, product=product)
        order_qs = Order.objects.all()
        self.model_admin.delete_queryset(rf.get("/"), order_qs)
        assert not Order.objects.exists()
        product_db = Product.objects.get(id=product.id)
        assert (
            product_db.quantity_in_stock
            == product.quantity_in_stock + item_1.quantity + item_2.quantity
        )

    def test_update_user_balance__old_payment_equals_new_payment(
        self, order, user_profile
    ):
        old_user_balance = user_profile.payment_balance
        self.model_admin.update_user_balance(order)
        user_profile.refresh_from_db()
        assert user_profile.payment_balance == old_user_balance

    def test_update_user_balance__new_payment_is_none(self, order, user_profile):
        order.paid_amount = 50
        order.save(update_fields=["paid_amount"])
        old_balance = order.order_balance
        order.paid_amount = None
        old_user_balance = user_profile.payment_balance
        self.model_admin.update_user_balance(order)
        user_profile.refresh_from_db()
        order.save(update_fields=["paid_amount"])
        order.refresh_from_db()
        assert user_profile.payment_balance == old_user_balance - old_balance

    def test_update_user_balance__old_payment_is_none(self, order, user_profile):
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        payment_value = 50
        order.paid_amount = payment_value
        old_user_balance = user_profile.payment_balance
        self.model_admin.update_user_balance(order)
        user_profile.refresh_from_db()
        assert user_profile.payment_balance == old_user_balance + order.order_balance

    def test_update_user_balance__payment_increased(self, order, user_profile):
        order.paid_amount = 40
        order.save(update_fields=["paid_amount"])
        increase_value = 60
        order.paid_amount += increase_value
        old_user_balance = user_profile.payment_balance
        self.model_admin.update_user_balance(order)
        user_profile.refresh_from_db()
        assert user_profile.payment_balance == old_user_balance + increase_value

    def test_save_model__change_is_true_calls_update_and_super(
        self, monkeypatch, order
    ):
        # arrange
        called = {"update_called": False, "super_called": False}

        def fake_update_user_balance(*, order):
            called["update_called"] = True

        def fake_super_save_model(self, request, obj, form, change):
            called["super_called"] = True
            # simulate DB save like the real super() would do
            obj.save()

        monkeypatch.setattr(
            OrderAdmin, "update_user_balance", staticmethod(fake_update_user_balance)
        )
        monkeypatch.setattr(
            DjangoModelAdmin, "save_model", fake_super_save_model, raising=True
        )

        # act
        self.model_admin.save_model(self.request, order, form=None, change=True)

        # assert
        assert called["update_called"] is True
        assert called["super_called"] is True

    def test_save_model__change_is_false_sets_number_calls_super_when_no_paid(
        self, monkeypatch, user
    ):
        # arrange
        order = OrderFactory.build(order_number=None, user=user, paid_amount=None)

        calculated_number = 123
        called = {"super_called": False}

        def fake_calculate_order_number(_Order):
            return calculated_number

        def fake_super_save_model(self, request, obj, form, change):
            called["super_called"] = True
            obj.save()

        # patch helpers and super
        from apps.form import admin as admin_module

        monkeypatch.setattr(
            admin_module,
            "calculate_order_number",
            fake_calculate_order_number,
            raising=True,
        )
        monkeypatch.setattr(
            DjangoModelAdmin, "save_model", fake_super_save_model, raising=True
        )

        # act
        self.model_admin.save_model(self.request, order, form=None, change=False)

        # assert
        order.refresh_from_db()
        assert order.order_number == calculated_number
        assert called["super_called"] is True

    def test_save_model__change_is_false_nulls_paid_and_shows_message(
        self, monkeypatch, user
    ):
        # arrange
        order = OrderFactory.build(
            order_number=None, user=user, paid_amount=Decimal("10")
        )

        calculated_number = 777
        messages_logged = []

        def fake_calculate_order_number(_Order):
            return calculated_number

        def fake_message_user(request, message, level):
            messages_logged.append((message, level))

        def fake_super_save_model(self, request, obj, form, change):
            obj.save()

        # patch helpers, message_user and super
        from apps.form import admin as admin_module

        monkeypatch.setattr(
            admin_module,
            "calculate_order_number",
            fake_calculate_order_number,
            raising=True,
        )
        monkeypatch.setattr(
            self.model_admin, "message_user", fake_message_user, raising=True
        )
        monkeypatch.setattr(
            DjangoModelAdmin, "save_model", fake_super_save_model, raising=True
        )

        # act
        self.model_admin.save_model(self.request, order, form=None, change=False)

        # assert
        order.refresh_from_db()
        # paid should be nulled on create
        assert order.paid_amount is None
        # order number assigned from calculator
        assert order.order_number == calculated_number
        # one error message with the expected text
        assert len(messages_logged) == 1
        msg, level = messages_logged[0]
        assert "Nie zapisano płatności podczas tworzenia zamówienia" in msg
        assert level == messages.ERROR

    def test_order_cost_with_fund(self, order):
        assert self.model_admin.order_cost_with_fund(order) == display_as_zloty(
            order.order_cost_with_fund
        )

    def test_user_balance(self, order, user_profile):
        assert self.model_admin.user_balance(order) == display_as_zloty(
            order.user_balance
        )

    def test_has_change_permission__paid(self, order, rf):
        assert order.paid_amount is not None
        assert self.model_admin.has_change_permission(rf.get("/"), order) is False

    def test_has_change_permission__not_paid(self, order, rf):
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        assert self.model_admin.has_change_permission(rf.get("/"), order) is True

    def test_has_change_permission__paid_0(self, order, rf):
        order.paid_amount = 0
        order.save(update_fields=["paid_amount"])
        assert self.model_admin.has_change_permission(rf.get("/"), order) is False


class TestOrderItemAdmin:
    @pytest.fixture(autouse=True)
    def _setup(self, admin_user, request_factory, admin_site):
        self.model_admin = OrderItemAdmin(OrderItem, admin_site)
        self.request = request_factory.post("/")
        self.request.user = admin_user

    def test_order_number(self, order, product):
        item = OrderItemFactory.create(order=order, product=product, quantity=1)
        assert self.model_admin.order_number(item) == f"{order.order_number}"

    def test_order_user(self, order, product):
        item = OrderItemFactory.create(order=order, product=product, quantity=1)
        assert self.model_admin.order_user(item) == f"{order.user.last_name}"

    def test_product_name(self, order, product):
        item = OrderItemFactory.create(order=order, product=product, quantity=1)
        assert self.model_admin.product_name(item) == f"{product.name}"

    def test_producer_short(self, order, product):
        item = OrderItemFactory.create(order=order, product=product, quantity=1)
        assert self.model_admin.producer_short(item) == f"{product.producer.short}"

    def test_has_delete_permission__no_obj(self, rf):
        assert self.model_admin.has_delete_permission(rf.get("/"), obj=None) is True

    def test_has_delete_permission__order_not_settled(self, rf, order, product):
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        item = OrderItemFactory.create(order=order, product=product, quantity=1)
        assert self.model_admin.has_delete_permission(rf.get("/"), obj=item) is True

    def test_has_delete_permission__order_settled(self, rf, order, product):
        assert order.paid_amount is not None
        item = OrderItemFactory.create(order=order, product=product, quantity=1)
        assert self.model_admin.has_delete_permission(rf.get("/"), obj=item) is False

    def test_delete_queryset__restores_stock_for_each_and_deletes(
        self, order, product, rf
    ):
        # Given
        order.paid_amount = None
        order.save(update_fields=["paid_amount"])
        item1 = OrderItemFactory.create(order=order, product=product, quantity=2)
        item2 = OrderItemFactory.create(order=order, product=product, quantity=4)
        qs = OrderItem.objects.filter(id__in=[item1.id, item2.id])

        with patch("apps.form.admin.reduce_product_stock") as reduce_patch:
            # When
            self.model_admin.delete_queryset(rf.post("/"), qs)

            # Then: called for each item and items deleted
            expected_calls = {
                (Product, item1.product.id, item1.quantity, True),
                (Product, item2.product.id, item2.quantity, True),
            }
            actual_calls = {
                (
                    call.args[0],
                    call.args[1],
                    call.args[2],
                    call.kwargs.get("negative", False),
                )
                for call in reduce_patch.call_args_list
            }
            assert expected_calls == actual_calls
            assert not OrderItem.objects.filter(id__in=[item1.id, item2.id]).exists()

    def test_delete_model__restores_stock_and_deletes(self, order, product, rf):
        # Given
        item = OrderItemFactory.create(order=order, product=product, quantity=3)
        with patch("apps.form.admin.reduce_product_stock") as reduce_patch:
            # When
            self.model_admin.delete_model(rf.post("/"), item)

            # Then
            reduce_patch.assert_called_once_with(
                Product, item.product.id, item.quantity, negative=True
            )
            assert not OrderItem.objects.filter(id=item.id).exists()
