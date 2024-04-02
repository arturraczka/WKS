from django.core.management.base import BaseCommand
from apps.form.models import Product
import logging

logger = logging.getLogger("django.server")


# NOT IN USE
class Command(BaseCommand):
    help = "Sets quantity_delivered_this_week attribute of all Products to 0"

    def handle(self, *args, **options):
        products = Product.objects.all()
        for product in products:
            product.quantity_delivered_this_week = 0
            product.save()

        logger.info("Products quantity_delivered_this_week set to 0.")
