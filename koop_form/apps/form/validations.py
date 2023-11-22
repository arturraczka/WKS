from django.db.models import Sum
from django.contrib import messages
from django.shortcuts import get_object_or_404

from apps.form.models import Product
from apps.form.services import (
    calculate_previous_friday,
    order_check,
)
from django.utils import timezone


def validate_product_already_in_order(product, request, order_model):
    previous_friday = calculate_previous_friday()
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


def validate_order_max_quantity(product, product_with_related, instance, request):
    previous_friday = calculate_previous_friday()
    order_max_quantity = product.order_max_quantity
    if order_max_quantity is not None:
        ordered_quantity = (
            product_with_related.orderitems.filter(
                order__date_created__gte=previous_friday
            )
            .exclude(pk=instance.id)
            .aggregate(ordered_quantity=Sum("quantity"))["ordered_quantity"]
        )
        if ordered_quantity is None:
            ordered_quantity = 0
        if order_max_quantity < ordered_quantity + instance.quantity:
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


# TODO to nie będzie potrzebne, gdy zrobię porządek z widokiem podsumowania zamówienia
def validate_weight_scheme(product_with_related, instance, request):
    if instance.quantity not in product_with_related.weight_schemes.all().values_list(
        "quantity", flat=True
    ):
        messages.warning(
            request,
            "Nieprawidłowa waga zamawianego produtku. Wybierz wagę z dostępnego schematu.",
        )
        return True


def perform_create_orderitem_validations(instance, request, order_model, product_model):
    product_from_form = instance.product
    product_with_related = get_object_or_404(
        product_model.objects.filter(pk=product_from_form.id).prefetch_related(
            "weight_schemes", "orderitems"
        )
    )
    if (
        validate_product_already_in_order(product_from_form, request, order_model)
        or validate_order_deadline(product_from_form, request)
        or validate_order_max_quantity(
            product_from_form, product_with_related, instance, request
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

    if (
        validate_weight_scheme(product_with_related, instance, request)
        or validate_order_deadline(product_from_form, request)
        or validate_order_max_quantity(
            product_from_form, product_with_related, instance, request
        )
    ):
        return False
    else:
        return True


def validate_order_exists(request):
    if order_check(request.user):
        messages.warning(request, "Masz już zamówienie na ten tydzień.")
        return True
