import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.contrib.messages import get_messages
from django.db.models import Case, When, F, Q

from apps.form.helpers import calculate_previous_weekday, koop_default_interval_start
from apps.core.models import AppConfig

logger = logging.getLogger("django.server")


def calculate_order_cost(orderitems):
    """Returns sum of order_item.quantity times product.price for given QS of OrderItem model."""
    order_cost = orderitems.annotate(
        item_cost=F("quantity") * F("product__price")
    ).aggregate(order_cost=Sum("item_cost"))["order_cost"]
    if order_cost is None:
        return 0
    return order_cost


def order_check(user):
    """Returns True if the user has an order created this week (counted from last Saturday 1:00 AM CEST)."""
    return user.orders.filter(date_created__gte=koop_default_interval_start()).exists()


def staff_check(user):
    """Returns True if User is staff member."""
    return user.is_staff


def list_messages(response):
    """Extracts messages from response object and returns them as a list."""
    messages = [msg.message for msg in list(get_messages(response.wsgi_request))]
    return messages


def calculate_order_number(order_model):
    """Returns order number as a sum of orders from this week + 1. Used for newly created Order instances."""
    return order_model.objects.filter(date_created__gte=koop_default_interval_start()).count() + 1


def recalculate_order_numbers(order_model, order_instance_date_created):
    """Retrieves queryset of Order instances newer than given date. Decrements order_number by 1
    for all instances. Used in signals in case of Order instance deletion to avoid order_number step other than 1.
    """
    if order_instance_date_created < koop_default_interval_start():
        return
    orders_qs = order_model.objects.filter(
        date_created__gt=order_instance_date_created
    ).order_by("date_created")
    orders_qs.update(order_number=F("order_number") - 1)


# TODO obviously suboptimal function. But used only in a reporting phase, so terrible performance should be acceptable.
def create_order_data_list(products):
    """For each ordered product this week globally creates a formatted list of orders with order number and ordered quantity."""
    config = AppConfig.load()
    order_data_list = []

    for product in products:
        orderitems_qs = (
            product.orderitems.filter(item_ordered_date__gte=config.report_interval_start, item_ordered_date__lte=config.report_interval_end)
            .order_by("order__order_number")
            .select_related("order")
        )
        order_data = ""
        for orderitem in orderitems_qs:
            order_data += f"(skrz{orderitem.order.order_number}: {Decimal(orderitem.quantity).normalize() + Decimal(0)}) "  # adding Decimal(0) escapes scientific notation formatting
        order_data_list.append(order_data)
    return order_data_list


def get_quantity_choices():
    """Generates choices for OrderItem quantity field."""
    choices = [
        (Decimal("0.000"), "0"),
        (Decimal("100"), "100"),
        (Decimal("25"), "25"),
        (Decimal("35"), "35"),
        (Decimal("45"), "45"),
    ]

    for x in range(1, 10):  # od 1 do 9
        choices.append((Decimal(f"0.0{x}0"), f"0.0{x}"))
        choices.append((Decimal(f"1.{x}00"), f"1.{x}"))
        choices.append((Decimal(f"2.{x}00"), f"2.{x}"))
        choices.append((Decimal(f"{x}.000"), f"{x}"))
        choices.append((Decimal(f"1{x}.000"), f"1{x}"))
        choices.append((Decimal(f"{x}0.000"), f"{x}0"))

    for x in range(3, 10):  # od 3 do 9
        choices.append((Decimal(f"{x}.500"), f"{x}.5"))

    for x in range(10, 100):  # od 10 do 99
        choices.append((Decimal(f"0.{x}0"), f"0.{x}"))

    return sorted(choices)


def get_producers_list(producer_model):
    """Builds a list of all active producers [slug, name] for a dropdown menu used in navigation between producers"""
    producers = producer_model.objects.filter(is_active=True).values("slug", "name")
    return [[producer["slug"], producer["name"]] for producer in producers]


def add_producer_list_to_context(context, producer_model):
    """Adds list of producers, next_producer and previous_producer to context[]. Used for navigation purposes."""
    context["producers"] = get_producers_list(producer_model)
    producer_index = context["producers"].index(
        [context["producer"].slug, context["producer"].name]
    )
    if producer_index != 0:
        context["previous_producer"] = context["producers"][producer_index - 1][0]
    else:
        context["previous_producer"] = None
    if producer_index + 1 != len(context["producers"]):
        context["next_producer"] = context["producers"][producer_index + 1][0]
    else:
        context["next_producer"] = None


def get_product_weight_schemes_list(product):
    """For a given product instance creates a list of tuples containing weight_scheme pairs. To be used as 'choices' in forms."""
    weight_schemes_quantity_list = []
    weight_schemes_set = product.weight_schemes.all()
    for weight_scheme in weight_schemes_set:
        weight_schemes_quantity_list.append(
            (
                Decimal(weight_scheme.quantity),
                f"{weight_scheme.quantity}".rstrip("0").rstrip("."),
            )
        )
    return [
        weight_schemes_quantity_list,
    ]


def add_weight_schemes_as_choices_to_forms(forms, products_weight_schemes):
    for form, scheme in zip(forms, products_weight_schemes):
        form.fields["quantity"].choices = scheme


def add_choices_to_form(form, product):
    """To OrderItem form instance adds choices for quantity field, based on targeted product's available weight_schemes."""
    product_weight_schemes_list = get_product_weight_schemes_list(product)
    form.fields["quantity"].choices = product_weight_schemes_list[0]


def filter_products_with_ordered_quantity_income_and_supply_income(
    product_model, producer_id, filter_producer=True
):
    """Returns a Product QS filtered for a given Producer instance, ordered by name, with annotated: ordered_quantity,
    income, supply_quantity, supply_income and excess. Limits resulting QS to fields: name, orderitems__quantity and
    supplyitems__quantity."""
    config = AppConfig.load()
    products = product_model.objects.only("name", "orderitems__quantity", "supplyitems__quantity")
    if filter_producer:
        products = products.filter(producer=producer_id)

    annotated_products = products.annotate(
            ordered_quantity=Sum(
                Case(
                    When(
                        Q(orderitems__item_ordered_date__gte=config.report_interval_start) & Q(orderitems__item_ordered_date__lte=config.report_interval_end),
                        then=F("orderitems__quantity"),
                    ),
                    default=Decimal(0),
                )
            ),
            income=F("ordered_quantity") * F("price"),
            supply_quantity=Case(
                When(
                    Q(supplyitems__date_created__gte=config.report_interval_start) & Q(supplyitems__date_created__lte=config.report_interval_end),
                    then=F("supplyitems__quantity"),
                ),
                default=Decimal(0),
            ),
            supply_income=F("supply_quantity") * F("price"),
            excess=F("supply_quantity") - F("ordered_quantity"),
        ).distinct().order_by("name")

    return annotated_products


def filter_products_with_ordered_quantity(product_model):
    """Returns a Product QS with annotated: ordered_quantity and income.
    Limits resulting QS to fields: name, orderitems__quantity and annotations."""
    config = AppConfig.load()
    products = product_model.objects.only("name", "is_stocked", "orderitems__quantity")

    annotated_products = products.annotate(
            ordered_quantity=Sum(
                "orderitems__quantity",
                filter=Q(orderitems__item_ordered_date__gte=config.report_interval_start) & Q(orderitems__item_ordered_date__lte=config.report_interval_end),
                default=0,
            ),
            income=F("ordered_quantity") * F("price"),
        ).distinct().order_by("name")

    return annotated_products


def filter_products_with_supplies_quantity(product_model):
    """Returns a Product QS with annotated: supply_quantity and supply_income.
    Limits resulting QS to fields: name, supplyitems__quantity and annotations."""
    report_interval_start = calculate_previous_weekday()
    report_interval_end = report_interval_start + timedelta(days=7)

    products = product_model.objects.only("name", "supplyitems__quantity")

    annotated_products = products.annotate(
            supply_quantity=Sum(
                "supplyitems__quantity",
                filter=Q(supplyitems__date_created__gte=report_interval_start) & Q(supplyitems__date_created__lte=report_interval_end),
                default=0,
            ),
            supply_income=F("supply_quantity") * F("price"),
        ).distinct().order_by("name")

    return annotated_products


def get_users_last_order(order_model, request_user):
    return order_model.objects.get(user=request_user, date_created__gte=calculate_previous_weekday())


def get_orderitems_query(orderitem_model, order_id):
    """Returns OrderItems QS related to given Order instance fetched with related Product, ordered by product__name.
    Limits resulting QS to fields: product_id, quantity, product__name and product__price.
    """
    return (
        orderitem_model.objects.filter(order=order_id)
        .select_related("product")
        .only("product_id", "quantity", "product__price", "product__name")
        .order_by("product__name")
    )


def get_orderitems_query_with_related_order(orderitem_model, order_id):
    """Returns OrderItems QS related to given Order instance fetched with related Product and Order, ordered by product__name.
    Limits resulting QS to fields: product_id, quantity, product__name and product__price.
    """
    return (
        orderitem_model.objects.filter(order=order_id)
        .select_related("product", "order")
        .only("quantity", "product__price", "product__name", "order__id")
        .order_by("product__name")
    )


def check_if_form_is_open():
    """Returns True if calling now() is between Saturday 12:00 and Monday 20:00. Used as indicator to blocking POST
    requests for Orders and OrderItems."""
    if settings.DEBUG:
        return True
    else:
        form_open = calculate_previous_weekday(3, 12)
        form_closed = form_open + timedelta(hours=56)
        today = datetime.now().astimezone()
        return form_open < today < form_closed


def reduce_product_stock(product_model, product_id, quantity, negative=False):
    """Reduces Product.quantity_in_stock according to OrderItem or SupplyItem quantity being saved.
    If negative=True, increases instead of reducing."""
    product_instance = product_model.objects.filter(id=product_id)
    if negative:
        quantity = -quantity
    product_instance.update(quantity_in_stock=F("quantity_in_stock") - quantity)


def alter_product_stock(
    product_model, product_id, new_quantity, model_id, model, negative=False
):
    """Increases or decreases Product.quantity_in_stock according to OrderItem or SupplyItem quantity changes.
    If negative=True, reverses the action."""
    model_instance = model.objects.get(id=model_id)
    product_instance = product_model.objects.filter(id=product_id)
    old_quantity = model_instance.quantity
    quantity_difference = new_quantity - old_quantity
    if negative:
        quantity_difference = -quantity_difference
    product_instance.update(
        quantity_in_stock=F("quantity_in_stock") - quantity_difference
    )


def display_as_zloty(value: Decimal) -> str:
    """
    Converts decimal value to string with precision to the first decimal place, adds currency zł,
    replaces dot for comma.
    """
    return f"{value:.1f} zł".replace(".", ",")
