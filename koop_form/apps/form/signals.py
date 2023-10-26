from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import IntegrityError

from apps.form.models import WeightScheme, Product


@receiver(post_save, sender=Product)
def add_zero_as_weight_scheme(sender, instance, **kwargs):
    weight_scheme_zero = WeightScheme.objects.get(quantity=0)
    instance.weight_schemes.add(weight_scheme_zero.id)
