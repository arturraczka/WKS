import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from factory import Faker, SubFactory, post_generation, RelatedFactory
from factory.django import DjangoModelFactory
import pytz
from apps.form.models import Producer, Product, Status, WeightScheme, Order, OrderItem
from django.utils import timezone

from apps.supply.models import Supply, SupplyItem
from apps.user.models import UserProfile, UserProfileFund


ModelUser = get_user_model()


class ProducerFactory(DjangoModelFactory):
    class Meta:
        model = Producer

    name = Faker("name")
    short = Faker("word")
    description = Faker("paragraph")
    order = Faker("random_int", min=1, max=10000)


class StatusFactory(DjangoModelFactory):
    class Meta:
        model = Status

    status_type = Faker("word")
    desc = Faker("paragraph")


class WeightSchemeFactory(DjangoModelFactory):
    class Meta:
        model = WeightScheme

    quantity = Faker("random_int", min=0, max=1000)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = ModelUser
        django_get_or_create = ("username",)

    username = Faker("name")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    email = Faker("email")
    password = Faker("password")


class UserProfileFundFactory(DjangoModelFactory):
    class Meta:
        model = UserProfileFund

    value = Faker(
        "pydecimal",
        left_digits=1,
        right_digits=2,
        min_value=Decimal("1.1"),
        max_value=Decimal("1.3"),
    )


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = SubFactory(UserFactory)
    fund = SubFactory(UserProfileFundFactory)
    koop_id = Faker("random_int", min=1, max=1000)
    phone_number = Faker("random_int", min=500000000, max=899999999)
    payment_balance = Faker(
        "pydecimal", left_digits=2, right_digits=2, min_value=Decimal("0")
    )


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user = SubFactory(UserFactory)
    pick_up_day = ["środa", "czwartek"][random.randint(0, 1)]
    date_created = timezone.now()
    is_given = False
    order_number = 1
    paid_amount = Faker(
        "pydecimal", left_digits=2, right_digits=2, min_value=Decimal("0")
    )

    @post_generation
    def products(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for product in extracted:
                self.products.add(product)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product
        django_get_or_create = ("name",)

    producer = SubFactory(ProducerFactory)
    name = Faker("name")
    description = Faker("paragraph")
    order_max_quantity = Faker("random_int", min=10, max=30)
    quantity_in_stock = Faker("random_int", min=0, max=10)
    price = Faker("random_int", min=1, max=40)
    order_deadline = Faker(
        "future_datetime", end_date="+30d", tzinfo=pytz.timezone("Europe/Warsaw")
    )
    quantity_delivered_this_week = -1
    is_active = True

    @post_generation
    def statuses(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for status in extracted:
                self.statuses.add(status)

    @post_generation
    def weight_schemes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for weight_scheme in extracted:
                self.weight_schemes.add(weight_scheme)


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = SubFactory(OrderFactory)
    product = SubFactory(ProductFactory)
    quantity = Faker("random_int", min=1, max=4)
    item_ordered_date = timezone.now()


class OrderWithProductFactory(OrderFactory):
    products = RelatedFactory(
        OrderItemFactory,
        factory_related_name="order",
    )


class SupplyFactory(DjangoModelFactory):
    class Meta:
        model = Supply

    producer = SubFactory(ProducerFactory)
    user = SubFactory(UserFactory)

    @post_generation
    def product(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for product in extracted:
                self.product.add(product)

    @post_generation
    def date_created(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            # write directly to DB to bypass auto_now_add
            type(self).objects.filter(pk=self.pk).update(date_created=extracted)
            self.refresh_from_db()


class SupplyItemFactory(DjangoModelFactory):
    class Meta:
        model = SupplyItem

    supply = SubFactory(SupplyFactory)
    product = SubFactory(ProductFactory)
    quantity = Faker("random_int", min=3, max=20)

    @post_generation
    def date_created(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            # write directly to DB to bypass auto_now_add
            type(self).objects.filter(pk=self.pk).update(date_created=extracted)
            self.refresh_from_db()
