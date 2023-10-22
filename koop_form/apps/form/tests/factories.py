from django.contrib.auth import get_user_model
from factory import Faker, SubFactory, post_generation, RelatedFactory
from factory.django import DjangoModelFactory
import pytz
from apps.form.models import Producer, Product, Status, WeightScheme, Order, OrderItem

ModelUser = get_user_model()


class ProducerFactory(DjangoModelFactory):
    class Meta:
        model = Producer

    name = Faker("name")
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


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user = SubFactory(UserFactory)
    pick_up_day = "Środa"
    date_created = Faker(
        "past_datetime", start_date="-2d", tzinfo=pytz.timezone("Europe/Warsaw")
    )
    total_price = Faker("random_int", min=1, max=40)
    is_given = False

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
    quantity_delivered_this_week = Faker("random_int", min=0, max=10)
    is_visible = True

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


class OrderWithProductFactory(OrderFactory):
    products = RelatedFactory(
        OrderItemFactory,
        factory_related_name="order",
    )
