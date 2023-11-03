import logging
from datetime import datetime, timedelta
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.contrib.messages import get_messages
from django.db.models import Q
from django.db.models import Case, When, F

logger = logging.getLogger()


# TODO: try/except w ogóle nie działa, nie przechwytuje MultipleObjectsReturned
def get_object_prefetch_related(model_class, *args, **kwargs):
    try:
        object_with_related = get_object_or_404(
            model_class.objects.filter(**kwargs).prefetch_related(*args)
        )
    except MultipleObjectsReturned:
        logger.error("User has two active Orders for this week!")
        return None
    return object_with_related


def filter_objects_prefetch_related(model_class, *args, **kwargs):
    objects_with_related = model_class.objects.filter(**kwargs).prefetch_related(*args)
    return objects_with_related


def filter_objects_select_related(model_class, *args, **kwargs):
    objects_with_related = model_class.objects.filter(**kwargs).select_related(*args)
    return objects_with_related


def calculate_previous_friday():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    friday = 4
    days_until_previous_friday = (friday + today.weekday() - 1) % 7
    previous_friday = today - timedelta(days=days_until_previous_friday)
    return previous_friday


def calculate_order_cost(orderitems):
    order_cost = 0
    for item in orderitems:
        order_cost += item.quantity * item.product.price
    return order_cost


def order_exists_test(request, order):
    previous_friday = calculate_previous_friday()
    return order.objects.filter(
        user=request.user, date_created__gte=previous_friday
    ).exists()


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


def add_0_as_weight_scheme(pk, product_model, weight_scheme_model):
    product_instance = product_model.objects.get(pk=pk)
    quantity_zero = weight_scheme_model.objects.get(quantity=1.000)
    product_instance.weight_schemes.set([quantity_zero])


def do_the_magic():
    pass
