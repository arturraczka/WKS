import logging

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify

from apps.form.services import get_quantity_choices


ModelUser = get_user_model()
logger = logging.getLogger("django.server")


class Producer(models.Model):
    name = models.CharField(unique=True)
    short = models.CharField(default="test")
    slug = models.CharField(unique=True, blank=True)
    description = models.TextField(max_length=1000)
    order = models.IntegerField(
        default=10
    )  # Default order or use choices for specific values
    is_active = models.BooleanField(default=True)
    not_arrived = models.BooleanField(default=False, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Producer, self).save(*args, **kwargs)


class WeightScheme(models.Model):
    quantity = models.DecimalField(max_digits=6, decimal_places=3, unique=True)

    class Meta:
        ordering = ["quantity"]

    def __str__(self):
        return str(self.quantity)


class Status(models.Model):
    status_type = models.CharField(max_length=100)
    desc = models.TextField()

    class Meta:
        ordering = ["status_type"]

    def __str__(self):
        return self.status_type


class Product(models.Model):
    producer = models.ForeignKey(
        Producer, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField()
    description = models.TextField(max_length=1000)

    order_max_quantity = models.DecimalField(
        max_digits=9, decimal_places=3, blank=True, null=True
    )
    quantity_in_stock = models.DecimalField(
        max_digits=9, decimal_places=3, null=True, blank=True
    )
    price = models.DecimalField(max_digits=7, decimal_places=2)
    order_deadline = models.DateTimeField(null=True, blank=True)
    quantity_delivered_this_week = models.DecimalField(
        max_digits=9, decimal_places=3, default=-1, null=True, blank=True
    )
    weight_schemes = models.ManyToManyField(
        WeightScheme, related_name="products", through="product_weight_schemes"
    )
    is_active = models.BooleanField(default=True)
    statuses = models.ManyToManyField(Status, related_name="products", blank=True)

    class Meta:
        ordering = ["producer__short", "name"]

    def __str__(self):
        return f"{self.producer.short}: {self.name}"


class product_weight_schemes(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    weightscheme = models.ForeignKey(WeightScheme, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product}: " f"{self.weightscheme}"


class Order(models.Model):
    PICKUP_CHOICES = [
        ("środa", "środa"),
        ("czwartek", "czwartek"),
    ]

    user = models.ForeignKey(ModelUser, on_delete=models.CASCADE, related_name="orders")
    products = models.ManyToManyField(
        Product, through="OrderItem", related_name="orders", blank=True
    )
    pick_up_day = models.CharField(max_length=10, choices=PICKUP_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    is_given = models.BooleanField(default=False)  # do I need this?
    order_number = models.IntegerField(blank=True)

    class Meta:
        ordering = ["-date_created"]
        indexes = [
            models.Index(fields=["date_created"]),
        ]

    def __str__(self):
        return f"{self.user.last_name}: {str(self.date_created)[:19]}"

    def get_absolute_url(self):
        absolute_url = reverse(
            "order-detail", kwargs={"pk": self.pk, "user": self.user}
        )
        return absolute_url


class OrderItem(models.Model):
    QUANTITY_CHOICES = get_quantity_choices()

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="orderitems"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="orderitems"
    )
    quantity = models.DecimalField(
        max_digits=6, decimal_places=3, choices=QUANTITY_CHOICES
    )
    item_ordered_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["product"]
        indexes = [
            models.Index(fields=["order", "product"]),
        ]

    def __str__(self):
        return f"{self.order}: {self.product}"


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
