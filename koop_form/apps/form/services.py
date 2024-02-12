import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum, Prefetch, Value
from django.contrib.messages import get_messages
from django.db.models import Q
from django.db.models import Case, When, F



logger = logging.getLogger("django.server")


def calculate_previous_weekday(day=4, hour=0):
    """Returns datetime object of a chosen day of a week within last 7 days. Defaults to Friday 00:00. Monday: 1, Tuesday: 7, Wednesday: 6,
    Thursday: 5, Friday: 4, Saturday: 3, Sunday: 2"""
    today = (
        datetime.now()
        .astimezone()
        .replace(hour=hour, minute=0, second=0, microsecond=0)
    )
    weekday = day
    days_until_previous_day = (weekday + today.weekday() - 1) % 7
    previous_day = today - timedelta(days=days_until_previous_day)
    return previous_day


# TODO this could be annotate() + aggregate()
def calculate_order_cost(orderitems):
    """Returns sum of order_item.quantity times product.price for given QS of OrderItem model."""
    order_cost = 0
    for item in orderitems:
        order_cost += item.quantity * item.product.price
    return order_cost


def order_check(user):
    """Returns True if the user has an order created this week (counted from last Friday)."""
    previous_friday = calculate_previous_weekday()
    return user.orders.filter(date_created__gte=previous_friday).exists()


def staff_check(user):
    """Returns True if User is staff member."""
    return user.is_staff


def list_messages(response):
    """Extracts messages from response object and returns them as a list."""
    messages = [msg.message for msg in list(get_messages(response.wsgi_request))]
    return messages


def calculate_available_quantity(products):
    """First, calculates previous friday.
    Next, to products queryset annotates ordered_quantity - sum of quantities ordered this week.
    Finally, annotates available_quantity: order_max_quantity minus ordered_quantity or quantity_in_stock.
    """
    previous_friday = calculate_previous_weekday()
    products_with_available_quantity = (
        products.annotate(
            ordered_quantity=Sum(
                "orderitems__quantity",
                filter=Q(orderitems__item_ordered_date__gte=previous_friday),
            )
        ).annotate(
            available_quantity=Case(
                When(
                    ordered_quantity=None,
                    then=Case(
                        When(order_max_quantity=None, then=F("quantity_in_stock")),
                        default=F("order_max_quantity"),
                    ),
                ),
                default=Case(
                    When(order_max_quantity=None, then=F("quantity_in_stock")),
                    default=F("order_max_quantity") - F("ordered_quantity"),
                ),
            ),
        )
    )
    return products_with_available_quantity


def calculate_order_number(order_model):
    """Returns order number as a sum of orders from this week + 1. Used for newly created Order instances."""
    previous_friday = calculate_previous_weekday()
    return order_model.objects.filter(date_created__gte=previous_friday).count() + 1


def recalculate_order_numbers(order_model, order_instance_date_created):
    """Retrieves queryset of Order instances newer than given date. Decrements order_number by 1
    for all instances. Used in signals in case of Order instance deletion to avoid order_number step other than 1.
    """
    previous_friday = calculate_previous_weekday()
    if order_instance_date_created < previous_friday:
        return
    orders_qs = order_model.objects.filter(
        date_created__gt=order_instance_date_created
    ).order_by("date_created")
    for order in orders_qs:
        order.order_number = F("order_number") - 1
        order.save()


def reduce_order_quantity(orderitem_model, product_pk, delivered_quantity):
    previous_friday = calculate_previous_weekday()

    delivered_quantity_lower_than_ordered_quantity = True
    while delivered_quantity_lower_than_ordered_quantity:
        orderitems = (
            orderitem_model.objects.filter(product=product_pk)
            .filter(Q(item_ordered_date__gte=previous_friday))
            .order_by("-item_ordered_date")
        )
        ordered_quantity = 0
        for item in orderitems:
            ordered_quantity += item.quantity

        if delivered_quantity < ordered_quantity:
            last_item = orderitems[0]
            if delivered_quantity < ordered_quantity - last_item.quantity:
                last_item.delete()
            else:
                diff_quantity = (
                    delivered_quantity - ordered_quantity + last_item.quantity
                )
                last_item.quantity = diff_quantity
                last_item.save()
        else:
            delivered_quantity_lower_than_ordered_quantity = False


def create_order_data_list(products):
    previous_friday = calculate_previous_weekday()
    order_data_list = []

    for product in products:
        orderitems_qs = (
            product.orderitems.filter(item_ordered_date__gte=previous_friday)
            .order_by("item_ordered_date")
            .select_related("order")
        )
        order_data = ""
        for orderitem in orderitems_qs:
            order_data += f"(skrz{orderitem.order.order_number}: {Decimal(orderitem.quantity).normalize()}) "
        order_data_list.append(order_data)
    return order_data_list


def switch_products_isactive_bool_value(producer_instance):
    product_qs = producer_instance.products.all()
    operator = True if producer_instance.is_active else False
    for product in product_qs:
        product.is_active = operator
        product.save()


def get_quantity_choices():
    choices = [
        (Decimal("0.000"), "0"),
    ]

    for x in range(1, 10):
        choices.append((Decimal(f"0.0{x}0"), f"0.0{x}"))
        choices.append((Decimal(f"0.{x}00"), f"0.{x}"))
        choices.append((Decimal(f"{x}.000"), f"{x}"))
        choices.append((Decimal(f"{x}.500"), f"{x}.5"))
        choices.append((Decimal(f"{x}0.000"), f"{x}0"))

    return sorted(choices)


# TODO do testu samodzielnego, nie w widokach! - w widokach też :p
def get_producers_list(producer_model):
    producers = producer_model.objects.filter(is_active=True).values("slug", "name")
    return [[producer["slug"], producer["name"]] for producer in producers]


def add_producer_list_to_context(context, producer_model):
    context["producers"] = get_producers_list(producer_model)
    producer_index = context["producers"].index([context["producer"].slug, context["producer"].name])
    if producer_index != 0:
        context["previous_producer"] = context["producers"][producer_index - 1][0]
    if producer_index + 1 != len(context["producers"]):
        context["next_producer"] = context["producers"][producer_index + 1][0]


def get_products_weight_schemes_list(products_with_available_quantity):
    products_weight_schemes_list = []
    for product in products_with_available_quantity:
        weight_schemes_set = product.weight_schemes.all()
        weight_schemes_quantity_list = [
            (
                Decimal(weight_scheme.quantity),
                f"{weight_scheme.quantity}".rstrip("0").rstrip("."),
            )
            for weight_scheme in weight_schemes_set
        ]
        products_weight_schemes_list.append(weight_schemes_quantity_list)
    return products_weight_schemes_list


# TODO zmienić nazwę na add_choices_to_forms - albo może nie
def add_weight_schemes_as_choices_to_forms(forms, products_weight_schemes):
    for form, scheme in zip(forms, products_weight_schemes):
        form.fields["quantity"].choices = scheme


def add_choices_to_form(form, product):
    """To OrderItem form instance adds choices for quantity field, based on targeted product's available weight_schemes."""
    product_weight_schemes_list = get_products_weight_schemes_list(product)
    form.fields["quantity"].choices = product_weight_schemes_list[0]


def filter_products_with_ordered_quantity_income_and_supply_income(
    product_model, producer_id
):
    previous_friday = calculate_previous_weekday()
    products = (
        product_model.objects.only(
            "name", "orderitems__quantity", "supplyitems__quantity"
        )
        .filter(producer=producer_id)
        .annotate(
            ordered_quantity=Sum(
                Case(
                    When(
                        orderitems__item_ordered_date__gte=previous_friday,
                        then=F("orderitems__quantity"),
                    ),
                    default=Decimal(0),
                )
            ),
            income=F("ordered_quantity") * F("price"),
            supply_quantity=Case(
                When(
                    supplyitems__date_created__gte=previous_friday,
                    then=F("supplyitems__quantity"),
                ),
                default=Decimal(0),
            ),
            supply_income=F("supply_quantity") * F("price"),
            excess=F("supply_quantity") - F("ordered_quantity"),
            # total_income=Sum('income')
        )
        .distinct()
        .order_by("name")
        # .iterator(chunk_size=1000)
    )
    return products


def get_users_last_order(order_model, request_user):
    previous_friday = calculate_previous_weekday()
    return order_model.objects.get(user=request_user, date_created__gte=previous_friday)


def get_orderitems_query(orderitem_model, order_id):
    return (
        orderitem_model.objects.filter(order=order_id)
        .select_related("product")
        .only("product_id", "quantity", "product__price", "product__name")
        .order_by("product__name")
    )


def get_orderitems_query_2(orderitem_model, order_id):
    return (
        orderitem_model.objects.filter(order=order_id)
        .select_related("product", "order")
        .only("quantity", "product__price", "product__name", "order__id")
        .order_by("product__name")
    )


def check_if_form_is_open():
    if settings.DEBUG:
        return True
    else:
        form_open = calculate_previous_weekday(3, 12)
        form_closed = form_open + timedelta(hours=56)
        today = datetime.now().astimezone()
        return form_open < today < form_closed
        # if form_open < today < form_closed:
        #     is_open = True
        # else:
        #     is_open = False
        # return is_open
