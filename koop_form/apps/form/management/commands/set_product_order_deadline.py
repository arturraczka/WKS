from django.core.management.base import BaseCommand
from datetime import timedelta, datetime
import logging
from apps.form.models import Product, Producer
from django.db.models import F


logger = logging.getLogger("django.server")


class Command(BaseCommand):
    help = (
        "Increments order_deadline attribute of all Products and Producers having order_deadline not null and being a past datetime, by 7 days."
        "Run this command as cronjob, best before enabling users to create orders (Saturday morning)."
    )

    def handle(self, *args, **options):
        delta = timedelta(7)
        producers = Producer.objects.filter(order_deadline__isnull=False).filter(
            order_deadline__lt=datetime.now().astimezone()
        )
        products = Product.objects.filter(order_deadline__isnull=False).filter(
            order_deadline__lt=datetime.now().astimezone()
        )

        for producer in producers:
            producer.order_deadline = F("order_deadline") + delta
            producer.save()

        for product in products:
            product.order_deadline = F("order_deadline") + delta
            product.save()
