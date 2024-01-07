import logging

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.form.models import Product, Producer


ModelUser = get_user_model()
logger = logging.getLogger("django.server")


class Supply(models.Model):
    product = models.ManyToManyField(
        Product, through="SupplyItem", related_name="supplies", blank=True
    )
    user = models.ForeignKey(
        ModelUser, on_delete=models.CASCADE, related_name="supplies"
    )
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, related_name="supplies"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["producer__short", "-date_created"]
        indexes = [
            models.Index(fields=["date_created"]),
        ]

    def __str__(self):
        return f"{self.producer.short}: {str(self.date_created)[:19]}"

    def get_absolute_url(self):
        return reverse("supply-products-form", kwargs={"slug": self.producer.slug})


class SupplyItem(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="supplyitems"
    )
    supply = models.ForeignKey(
        Supply, on_delete=models.CASCADE, related_name="supplyitems"
    )
    quantity = models.DecimalField(max_digits=6, decimal_places=3)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["supply", "-date_created"]

    def __str__(self):
        return f"{self.product.producer.short}: {self.product.name}: {str(self.date_created)[:19]}"
