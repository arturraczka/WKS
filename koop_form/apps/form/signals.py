import logging

from django.db.models.signals import post_save, pre_delete, pre_save, post_delete
from django.dispatch import receiver

from apps.form.models import WeightScheme, Product, Order, OrderItem
from apps.form.services import recalculate_order_numbers


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


@receiver(post_save, sender=OrderItem)
def update_order_amount_if_created(sender, instance, created, **kwargs):
    if created:
        instance_amount = instance.quantity * instance.product.price
        order = Order.objects.get(id=instance.order.id)
        order.amount += instance_amount
        order.amount_with_fund = order.amount * order.user.userprofile.fund
        order.save()



@receiver(pre_save, sender=OrderItem)
def update_order_amount_if_edited(sender, instance, **kwargs):
    try:
        item_db = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        diff = instance.quantity - item_db.quantity
        order = Order.objects.get(id=instance.order.id)
        order.amount = order.amount + (diff * instance.product.price)
        order.amount_with_fund = order.amount * order.user.userprofile.fund
        order.save()


@receiver(post_delete, sender=OrderItem)
def update_order_amount_if_deleted(sender, instance, **kwargs):
    instance_amount = instance.quantity * instance.product.price
    instance.order.amount = instance.order.amount - instance_amount
    instance.order.amount_with_fund = instance.order.amount * instance.order.user.userprofile.fund
    instance.order.save()


@receiver(pre_save, sender=Order)
def update_order_difference(sender, instance, **kwargs):
    if instance.cash:
        instance.difference = instance.cash - instance.amount_with_fund
    else:
        instance.cash = 0
        instance.difference = - instance.amount_with_fund
    if instance.paid:
        instance.credit = instance.paid - instance.amount_with_fund
    else:
        instance.paid = 0
        instance.credit = - instance.amount_with_fund

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


# @receiver(pre_save, sender=Order)
# def assign_order_number(sender, instance, **kwargs):
#     if instance.order_number is None:
#         instance.order_number = calculate_order_number(sender)


# @receiver(post_save, sender=OrderItem)
# def delete_instance_if_quantity_eq_0(sender, instance, **kwargs):
#     if instance.quantity == 0:
#         orderitem_db = sender.objects.get(id=instance.id)
#         orderitem_db.delete()


@receiver(pre_delete, sender=Order)
def on_order_delete_trigger_recalculate_order_numbers(sender, instance, **kwargs):
    recalculate_order_numbers(sender, instance.date_created)


# @receiver(post_save, sender=Producer)
# def check_before_set_products_quantity_to_0(sender, instance, **kwargs):
#     if instance.not_arrived:
#         set_products_quantity_to_0(instance)
#         instance.not_arrived = False


# NOT IN USE
# @receiver(pre_save, sender=Producer)
# def check_before_switch_products_isactive_bool_value(sender, instance, **kwargs):
#     try:
#         producer_db = sender.objects.get(pk=instance.pk)
#     except sender.DoesNotExist:
#         pass
#     else:
#         if producer_db.is_active != instance.is_active:
#             switch_products_isactive_bool_value(instance)
