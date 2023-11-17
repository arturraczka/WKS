import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify

from apps.form.services import calculate_order_number, reduce_order_quantity, recalculate_order_numbers, \
    set_products_quantity_to_0, switch_products_isactive_bool_value

ModelUser = get_user_model()
logger = logging.getLogger("django.server")


class Producer(models.Model):
    name = models.CharField(unique=True)
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

        if self.pk is not None:
            if self.not_arrived is True:
                set_products_quantity_to_0(Product, self.pk)  # czy tego typu taski powinny być atomic_requestem?
                self.not_arrived = False

            producer_db = Producer.objects.get(pk=self.pk)
            if producer_db.is_active != self.is_active:  # czy tego typu taski powinny być atomic_requestem?
                switch_products_isactive_bool_value(Product, self.pk, self.is_active)

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
    name = models.CharField(unique=True)
    description = models.TextField(max_length=1000)

    order_max_quantity = models.DecimalField(
        max_digits=9, decimal_places=3, blank=True, default=9999
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
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk is not None:
            product_db = Product.objects.get(pk=self.pk)
            if (
                product_db.quantity_delivered_this_week
                != self.quantity_delivered_this_week
            ):
                reduce_order_quantity(
                    OrderItem, self.pk, self.quantity_delivered_this_week
                )  # czy tego typu taski powinny być atomic_requestem?
                self.quantity_delivered_this_week = -1
        super(Product, self).save(*args, **kwargs)


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
        return f"{self.user}: " f"Order: {self.pk}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.order_number = calculate_order_number(Order)
        super(Order, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        recalculate_order_numbers(Order, self.date_created, self.order_number)    # czy tego typu taski powinny być atomic_requestem?
        super(Order, self).delete(using=using, keep_parents=keep_parents)

    def get_absolute_url(self):
        absolute_url = reverse(
            "order-detail", kwargs={"pk": self.pk, "user": self.user}
        )
        return absolute_url


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="orderitems"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="orderitems"
    )
    quantity = models.DecimalField(max_digits=6, decimal_places=3)
    item_ordered_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["product"]
        indexes = [
            models.Index(fields=["order", "product"]),
        ]

    def __str__(self):
        return f"{self.order}: " f"{self.product}"

    def save(self, *args, **kwargs):
        if self.quantity == 0:
            try:
                self.delete()
            except ValueError:
                return None
        else:
            super(OrderItem, self).save(*args, **kwargs)
