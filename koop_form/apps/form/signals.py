from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.form.models import WeightScheme, Product, OrderItem
from apps.form.services import reduce_order_quantity

import logging

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


@receiver(pre_save, sender=Product)
def check_before_reduce_order_quantity(sender, instance, **kwargs):
    if instance.quantity_delivered_this_week != -1:
        product_db = sender.objects.get(pk=instance.id)

        if (
                product_db.quantity_delivered_this_week
                != instance.quantity_delivered_this_week
        ):
            reduce_order_quantity(
                OrderItem, instance.id, instance.quantity_delivered_this_week
            )
            instance.quantity_delivered_this_week = -1
            instance.save()
