from django.core.management.base import BaseCommand
from datetime import timedelta
import logging

from apps.form.models import Producer, Product
from apps.form.services import calculate_previous_weekday

logger = logging.getLogger("django.server")


class Command(BaseCommand):
    help = ("sets Products of JEdynie (Producer id=6) order_deadline value to next Monday 20:00. "
            "Run this command as cronjob, best before enabling users to create orders (Saturday morning).")

    def handle(self, *args, **options):
        previous_monday = calculate_previous_weekday(1, 20)
        delta = timedelta(7)
        next_monday = previous_monday + delta

        jedynie = Producer.objects.get(id=6)
        products = Product.objects.filter(producer=jedynie)

        for product in products:
            product.order_deadline = next_monday
            product.save()
