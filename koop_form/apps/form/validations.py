from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.form.models import Product
from apps.form.services import (
    calculate_previous_weekday,
    order_check,
)


def validate_product_already_in_order(product, request, order_model):
    previous_friday = calculate_previous_weekday()
    order_with_products = get_object_or_404(
        order_model.objects.filter(
            user=request.user, date_created__gte=previous_friday
        ).prefetch_related("products")
    )

    if order_with_products.products.filter(
        pk=product.id,
    ).exists():
        messages.warning(
            request, f"{product.name}: Dodałeś już ten produkt do zamówienia."
        )
        return True


def validate_order_max_quantity(product, product_instance, form_instance, request):
    """Validates whether created/updated orderitem.quantity exceeds product.quantity_in_stock or product.quantity_in_stock"""
    previous_friday = calculate_previous_weekday()
    if product.order_max_quantity is not None:
        ordered_quantity = (
            product_instance.orderitems.filter(order__date_created__gte=previous_friday)
            .exclude(pk=form_instance.id)
            .aggregate(ordered_quantity=Sum("quantity"))["ordered_quantity"]
        )
        if ordered_quantity is None:
            ordered_quantity = 0
        if product.order_max_quantity < ordered_quantity + form_instance.quantity:
            messages.warning(
                request,
                f"{product.name}: Przekroczona maksymalna ilość lub waga zamawianego produktu. Nie ma tyle.",
            )
            return True

    if product.quantity_in_stock is not None:
        try:
            item_db = product_instance.orderitems.get(pk=form_instance.id)
            quantity_delta = form_instance.quantity - item_db.quantity
        except ObjectDoesNotExist:
            quantity_delta = form_instance.quantity
        if product.quantity_in_stock < quantity_delta:
            messages.warning(
                request,
                f"{product.name}: Przekroczona maksymalna ilość lub waga zamawianego produktu. Nie ma tyle.",
            )
            return True


def validate_order_deadline(product, request):
    if product.order_deadline and product.order_deadline < timezone.now():
        messages.warning(
            request,
            f"{product.name}: Termin minął, nie możesz już dodać tego produktu do zamówienia.",
        )
        return True


def perform_create_orderitem_validations(
    form_instance, request, order_model, product_model
):
    related_product = form_instance.product
    product_instance = get_object_or_404(
        product_model.objects.filter(pk=related_product.id).prefetch_related(
            "weight_schemes", "orderitems"
        )
    )
    if (
        validate_product_already_in_order(related_product, request, order_model)
        or validate_order_deadline(related_product, request)
        or validate_order_max_quantity(
            related_product, product_instance, form_instance, request
        )
    ):
        return False
    return True


def perform_update_orderitem_validations(instance, request):
    product_from_form = instance.product

    product_with_related = get_object_or_404(
        Product.objects.filter(pk=product_from_form.id).prefetch_related(
            "weight_schemes", "orderitems"
        )
    )

    if validate_order_deadline(
        product_from_form, request
    ) or validate_order_max_quantity(
        product_from_form, product_with_related, instance, request
    ):
        return False
    else:
        return True


def validate_order_exists(request):
    if order_check(request.user):
        messages.warning(request, "Masz już zamówienie na ten tydzień.")
        return True


def validate_supply_exists(supply_model, producer_instance):
    previous_friday = calculate_previous_weekday()
    return (
        supply_model.objects.filter(producer=producer_instance)
        .filter(date_created__gte=previous_friday)
        .exists()
    )


def validate_supplyitem_exists(product_instance, supplyitem_model):
    previous_friday = calculate_previous_weekday()
    return (
        supplyitem_model.objects.filter(product=product_instance)
        .filter(date_created__gte=previous_friday)
        .exists()
    )
