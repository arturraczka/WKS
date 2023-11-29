import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.contrib.messages import get_messages
from django.db.models import Q
from django.db.models import Case, When, F


logger = logging.getLogger("django.server")


def calculate_previous_friday():
    """Returns datetime object of last Friday."""
    today = (
        datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    )
    friday = 4
    days_until_previous_friday = (friday + today.weekday() - 1) % 7
    previous_friday = today - timedelta(days=days_until_previous_friday)
    return previous_friday


def calculate_order_cost(orderitems):
    """Returns sum of order_item.quantity times product.price for given QS of OrderItem model."""
    order_cost = 0
    for item in orderitems:
        order_cost += item.quantity * item.product.price
    return order_cost


def order_check(user):
    """Returns True if the user has an order created this week (counted from last Friday)."""
    previous_friday = calculate_previous_friday()
    return user.orders.filter(date_created__gte=previous_friday).exists()


def staff_check(user):
    """Returns True if User is staff member."""
    return user.is_staff


def list_messages(response):
    messages = [msg.message for msg in list(get_messages(response.wsgi_request))]
    return messages


def calculate_available_quantity(products):
    previous_friday = calculate_previous_friday()

    products_with_available_quantity = products.annotate(
        ordered_quantity=Sum(
            "orderitems__quantity",
            filter=Q(orderitems__item_ordered_date__gte=previous_friday),
        ),
        available_quantity=Case(
            When(ordered_quantity=None, then=F("order_max_quantity")),
            default=F("order_max_quantity") - F("ordered_quantity"),
        ),
    ).order_by("name")

    return products_with_available_quantity


def calculate_order_number(order):
    order_number = 1
    previous_friday = calculate_previous_friday()
    order_count = order.objects.filter(date_created__gte=previous_friday).count()
    order_number += order_count
    return order_number


def calculate_total_income(products):
    total_income = 0
    for product in products:
        try:
            total_income += product.income
        except TypeError:
            logger.error("Error in counting total income for an order.")
            pass
    return total_income


def reduce_order_quantity(orderitem_model, product_pk, quantity):
    previous_friday = calculate_previous_friday()

    delivered_quantity_lower_than_ordered_quantity = True
    while delivered_quantity_lower_than_ordered_quantity:
        orderitems = (
            orderitem_model.objects.filter(product=product_pk)
            .filter(Q(item_ordered_date__gte=previous_friday))
            .order_by("item_ordered_date")
        )
        ordered_quantity = 0
        for item in orderitems:
            ordered_quantity += item.quantity

        if quantity < ordered_quantity:
            orderitems.reverse()[0].delete()
        else:
            # remnant = quantity - ordered_quantity
            delivered_quantity_lower_than_ordered_quantity = False


def recalculate_order_numbers(order_model, date, number):
    previous_friday = calculate_previous_friday()
    if date < previous_friday:
        return
    orders_qs = order_model.objects.filter(date_created__gt=date).order_by(
        "date_created"
    )
    initial = number
    for order in orders_qs:
        order.order_number = initial
        order.save()
        initial += 1


def create_order_data_list(products, order_model, orderitem_model):
    previous_friday = calculate_previous_friday()
    order_data_list = []
    for product in products:
        orders_qs = (
            order_model.objects.filter(products=product)
            .filter(date_created__gte=previous_friday)
            .order_by("order_number")
        )
        order_data = ""
        for order in orders_qs:
            orderitem = orderitem_model.objects.filter(order=order).get(product=product)
            order_data += f"(skrz{order.order_number}: {Decimal(orderitem.quantity).normalize()}) "
        order_data_list.append(order_data)
    return order_data_list


def set_products_quantity_to_0(producer_instance):
    """docstrings"""
    product_qs = producer_instance.products.all()
    for product in product_qs:
        product.quantity_delivered_this_week = 0
        product.save()


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


def get_producers_list(producer_model):
    producers = producer_model.objects.filter(is_active=True).values("slug", "name")
    return [[producer["slug"], producer["name"]] for producer in producers]


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


def add_weight_schemes_as_choices_to_forms(forms, products_weight_schemes):
    for form, scheme in zip(forms, products_weight_schemes):
        form.fields["quantity"].choices = scheme


def add_choices_to_forms(forms, products):
    products_weight_schemes_list = get_products_weight_schemes_list(products)
    add_weight_schemes_as_choices_to_forms(forms, products_weight_schemes_list)


def add_choices_to_form(form, product):
    """To OrderItem form instance adds choices for quantity field, based on targeted product's available weight_schemes.
    """
    product_weight_schemes_list = get_products_weight_schemes_list(product)
    form.fields["quantity"].choices = product_weight_schemes_list[0]


def filter_products_with_ordered_quantity_and_income(product_model, producer_instance):
    previous_friday = calculate_previous_friday()

    products = (
        product_model.objects.prefetch_related("orderitems")
        .only("name", "orderitems__quantity")
        .filter(producer=producer_instance)
        .filter(Q(orderitems__item_ordered_date__gte=previous_friday))
        .annotate(
            ordered_quantity=Sum("orderitems__quantity"),
            income=F("ordered_quantity") * F("price"),
        )
    )
    return products


def get_users_last_order(order_model, request_user):
    previous_friday = calculate_previous_friday()
    return order_model.objects.get(
            user=request_user, date_created__gte=previous_friday
        )


def get_orderitems_query(orderitem_model, order_id):
    return (
        orderitem_model.objects.filter(order=order_id)
        .select_related("product")
        .only("product_id", "quantity", "product__price", "product__name")
        .order_by("product__name")
    )
