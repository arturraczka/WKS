from django.core.management.base import BaseCommand
from datetime import timedelta
import logging
from apps.form.models import Product
from django.db.models import F


logger = logging.getLogger("django.server")


class Command(BaseCommand):
    help = (
        "Increments order_deadline attribute of all Products having order_deadline by 7 days."
        "Run this command as cronjob, best before enabling users to create orders (Saturday morning)."
    )

    def handle(self, *args, **options):
        delta = timedelta(7)
        products = Product.objects.filter(order_deadline__isnull=False).iterator(
            chunk_size=50
        )

        for product in products:
            product.order_deadline = F("order_deadline") + delta
            product.save()