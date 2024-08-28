import logging


from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from apps.form.models import WeightScheme, Product, Order
from apps.form.services import recalculate_order_numbers

logger = logging.getLogger("django.server")

class NotAllowedDeletionException(Exception):
    pass

def init_weight_scheme_with_zero(sender, **kwargs):
    _, created = WeightScheme.objects.get_or_create(quantity=0)
    if created:
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

@receiver(pre_delete, sender=Order)
def on_order_delete_trigger_recalculate_order_numbers(sender, instance, **kwargs):
    recalculate_order_numbers(sender, instance.date_created)
