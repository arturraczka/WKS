import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.contrib.messages import get_messages
from django.db.models import Q
from django.db.models import Case, When, F

logger = logging.getLogger("django.server")

# TODO tutaj wszystko muszę sprawdzić, czy jest testowane czy nie


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


# TODO to by się przydało przetestować, bo nie sądzę, żebym to testował w widokach hmmm
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
    orders_qs = order_model.objects.filter(date_created__gt=date).order_by('date_created')
    initial = number
    for order in orders_qs:
        # logger.info(initial)
        order.order_number = initial
        order.save()
        initial += 1


def create_order_data_list(products, order_model, orderitem_model):
    order_data_list = []
    for product in products:
        orders_qs = order_model.objects.filter(products=product).order_by('order_number')
        order_data = ''
        for order in orders_qs:
            orderitem = orderitem_model.objects.filter(order=order).get(product=product)
            order_data += f'(skrz{order.order_number}: {Decimal(orderitem.quantity).normalize()}) '
        order_data_list.append(order_data)
    return order_data_list


def set_products_quantity_to_0(product_model, pk):
    product_qs = product_model.objects.filter(producer=pk)
    for product in product_qs:
        product.quantity_delivered_this_week = 0
        product.save()
