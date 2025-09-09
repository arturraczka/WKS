import logging

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.form.models import Product, Producer


ModelUser = get_user_model()
logger = logging.getLogger("django.server")


class Supply(models.Model):
    product = models.ManyToManyField(
        Product,
        through="SupplyItem",
        related_name="supplies",
        blank=True,
        verbose_name="produkt",
    )
    user = models.ForeignKey(
        ModelUser,
        on_delete=models.CASCADE,
        related_name="supplies",
        verbose_name="użytkownik",
    )
    producer = models.ForeignKey(
        Producer,
        on_delete=models.CASCADE,
        related_name="supplies",
        verbose_name="producent",
    )
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="utworzono")

    class Meta:
        verbose_name = "Dostawa"
        verbose_name_plural = "Dostawy"
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
        Product,
        on_delete=models.CASCADE,
        related_name="supplyitems",
        verbose_name="produkt",
    )
    supply = models.ForeignKey(
        Supply,
        on_delete=models.CASCADE,
        related_name="supplyitems",
        verbose_name="dostawa",
    )
    quantity = models.DecimalField(max_digits=6, decimal_places=3, verbose_name="ilość")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="utworzono")

    class Meta:
        verbose_name = "Produkt w dostawie"
        verbose_name_plural = "Produkty w dostawie"
        ordering = ["supply", "-date_created"]

    def __str__(self):
        return f"{self.product.producer.short}: {self.product.name}: {str(self.date_created)[:19]}"
