import logging

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

from apps.form.models import WeightScheme, Product, OrderItem, Order, Producer
from apps.form.services import (
    reduce_order_quantity,
    calculate_order_number,
    recalculate_order_numbers,
    set_products_quantity_to_0,
    switch_products_isactive_bool_value,
)


logger = logging.getLogger("django.server")


@receiver(post_save, sender=Product)
def add_zero_as_weight_scheme(sender, instance, **kwargs):
    try:
        weight_scheme_zero = WeightScheme.objects.get(quantity=0)
    except WeightScheme.DoesNotExist:
        weight_scheme_zero = WeightScheme(quantity=0)
        weight_scheme_zero.save()
        weight_scheme_zero = WeightScheme.objects.get(quantity=0)
    instance.weight_schemes.add(weight_scheme_zero.id)


# @receiver(pre_save, sender=Product)
# def check_before_reduce_order_quantity(sender, instance, **kwargs):
#     if instance.quantity_delivered_this_week != -1:
#         product_db = sender.objects.get(pk=instance.id)
#
#         if (
#             product_db.quantity_delivered_this_week
#             != instance.quantity_delivered_this_week
#         ):
#             reduce_order_quantity(
#                 OrderItem, instance.id, instance.quantity_delivered_this_week
#             )
#             instance.quantity_delivered_this_week = -1


@receiver(pre_save, sender=Order)
def assign_order_number(sender, instance, **kwargs):
    if instance.order_number is None:
        instance.order_number = calculate_order_number(sender)


@receiver(post_save, sender=OrderItem)
def delete_instance_if_quantity_eq_0(sender, instance, **kwargs):
    if instance.quantity == 0:
        orderitem_db = sender.objects.get(id=instance.id)
        orderitem_db.delete()


@receiver(pre_delete, sender=Order)
def on_order_delete_trigger_recalculate_order_numbers(sender, instance, **kwargs):
    recalculate_order_numbers(sender, instance.date_created)


@receiver(post_save, sender=Producer)
def check_before_set_products_quantity_to_0(sender, instance, **kwargs):
    if instance.not_arrived:
        set_products_quantity_to_0(instance)
        instance.not_arrived = False


@receiver(pre_save, sender=Producer)
def check_before_switch_products_isactive_bool_value(sender, instance, **kwargs):
    try:
        producer_db = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if producer_db.is_active != instance.is_active:
            switch_products_isactive_bool_value(instance)


@receiver(pre_save, sender=OrderItem)
def adjust_product_in_stock_quantity(sender, instance, **kwargs):
    product = Product.objects.get(id=instance.product.id)
    if product.quantity_in_stock is not None:
        try:
            item_db = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            if product.quantity_in_stock is not None:
                product.quantity_in_stock -= instance.quantity
                product.save()
        else:
            if instance.quantity is not None:
                ordered_quantity = item_db.quantity
                quantity_delta = instance.quantity - ordered_quantity
                product.quantity_in_stock -= quantity_delta
                product.save()
