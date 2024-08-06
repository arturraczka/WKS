import logging


from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from apps.form.models import WeightScheme, Product, Order, product_weight_schemes
from apps.form.services import recalculate_order_numbers

logger = logging.getLogger("django.server")


class NotAllowedDeletionException(Exception):
    pass

def init_weight_scheme_with_zero(sender, **kwargs):
    if not WeightScheme.objects.filter(quantity=0).exists():
        WeightScheme(quantity=0).save()
        logger.info('Database populated with WeightScheme quantity=0.')
    else:
        logger.info(f'Database already has WeightScheme quantity=0. {sender}')

@receiver(post_save, sender=Product)
def add_zero_as_weight_scheme(sender, instance,**kwargs):
    if WeightScheme.objects.filter(quantity=0).exists():
        instance.weight_schemes.add(WeightScheme.objects.get(quantity=0))

@receiver(pre_delete, sender=WeightScheme)
def add_zero_as_weight_scheme_deletion_prevent(sender, instance,**kwargs):
    if WeightScheme.objects.filter(quantity=0).first() == instance:
        raise NotAllowedDeletionException("WeigthScheme=0 cannot be deleted")

@receiver(pre_delete, sender=product_weight_schemes)
def add_zero_as_product_weight_scheme_deletion_prevent(sender, instance,**kwargs):
    if WeightScheme.objects.filter(quantity=0).first() == instance.weightscheme:
        raise NotAllowedDeletionException("WeigthScheme=0 cannot be deleted in Product")


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
