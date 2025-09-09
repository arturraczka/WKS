import logging
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify

from apps.form.managers import OrderManager
from apps.form.services import get_quantity_choices
from apps.user.services import get_user_fund

ModelUser = get_user_model()
logger = logging.getLogger("django.server")


class Producer(models.Model):
    name = models.CharField(unique=True, max_length=100, verbose_name="Nazwa")
    short = models.CharField(
        default="test", max_length=16, verbose_name="Nazwa skrócona"
    )  # to powinno być unique and indexed
    slug = models.CharField(unique=True, blank=True, max_length=100)
    description = models.TextField(max_length=1000, verbose_name="Opis")
    order = models.IntegerField(
        default=10, verbose_name="Kolejność"
    )  # Default order or use choices for specific values
    is_active = models.BooleanField(default=True, verbose_name="Czy aktywny")
    not_arrived = models.BooleanField(
        default=False, blank=True, verbose_name="Nie dojechał?"
    )
    manager_name = models.CharField(
        blank=True, null=True, max_length=100, verbose_name="Nazwa koordynatora"
    )
    manager_email = models.EmailField(
        blank=True, null=True, verbose_name="Email koordynatora"
    )
    manager_phone = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Numer koordynatora"
    )
    order_deadline = models.DateTimeField(
        null=True, blank=True, verbose_name="Deadline zamawiania"
    )

    class Meta:
        verbose_name = "Producent"
        verbose_name_plural = "Producenci"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Producer, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products", kwargs={"slug": self.slug})


class WeightScheme(models.Model):
    quantity = models.DecimalField(
        max_digits=6, decimal_places=3, unique=True, verbose_name="Ilość"
    )

    class Meta:
        verbose_name = "Schemat wagowy"
        verbose_name_plural = "Schematy wagowe"
        ordering = ["quantity"]

    def __str__(self):
        return str(self.quantity)

    def delete(self, *args, **kwargs):
        if not self.quantity == 0:
            super().delete(*args, **kwargs)


class Status(models.Model):
    status_type = models.CharField(max_length=100, verbose_name="Typ statusu")
    desc = models.TextField(verbose_name="Opis")

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Statusy"
        ordering = ["status_type"]

    def __str__(self):
        return self.status_type


class Category(models.Model):
    name = models.CharField(max_length=24, unique=True, verbose_name="Nazwa")

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"

    def __str__(self):
        return self.name


class Product(models.Model):
    unit_choices = [
        ("S", "S"),
        ("W", "W"),
        ("G", "G"),
    ]
    producer = models.ForeignKey(
        Producer,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Producent",
    )
    name = models.CharField(max_length=100, unique=True, verbose_name="Nazwa")
    description = models.TextField(
        max_length=250, null=True, blank=True, verbose_name="Opis"
    )

    order_max_quantity = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name="Ile maksymalnie można zamówić",
    )
    quantity_in_stock = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Ilość na magazynie",
    )
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Cena")
    order_deadline = models.DateTimeField(
        null=True, blank=True, verbose_name="Deadline zamawiania"
    )
    quantity_delivered_this_week = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        default=0,
        null=True,
        blank=True,
        verbose_name="Dostarczona ilość w tym tygodniu",
    )
    weight_schemes = models.ManyToManyField(
        WeightScheme,
        related_name="products",
        through="product_weight_schemes",
        verbose_name="Schematy wagowe",
    )
    is_active = models.BooleanField(default=True, verbose_name="Czy jest aktywny")
    statuses = models.ManyToManyField(
        Status, related_name="products", blank=True, verbose_name="Statusy"
    )
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.PROTECT,
        null=True,
        verbose_name="Kategoria",
    )
    subcategory = models.CharField(
        null=True, blank=True, max_length=100, verbose_name="Podkategoria"
    )
    unit = models.CharField(
        choices=unit_choices, max_length=100, verbose_name="Jednostka"
    )
    info = models.TextField(
        max_length=255, null=True, blank=True, verbose_name="Informacje"
    )
    is_stocked = models.BooleanField(
        default=False, verbose_name="Czy jest magazynowany"
    )

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}"


class product_weight_schemes(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Produkt"
    )
    weightscheme = models.ForeignKey(
        WeightScheme, on_delete=models.CASCADE, verbose_name="Schemat wagowy"
    )

    def __str__(self):
        return f"{self.product}: " f"{self.weightscheme}"

    def save(self, *args, **kwargs):
        if self.pk:
            self_db = product_weight_schemes.objects.get(pk=self.pk)
            if self.weightscheme.quantity != 0 and self_db.weightscheme.quantity == 0:
                return
        if not product_weight_schemes.objects.filter(
            product=self.product, weightscheme=self.weightscheme
        ).exists():
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if not self.weightscheme.quantity == 0:
            super().delete(*args, **kwargs)


class Order(models.Model):
    PICKUP_CHOICES = [
        ("środa", "środa"),
        ("czwartek", "czwartek"),
    ]

    user = models.ForeignKey(
        ModelUser,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Użytkownik",
    )
    products = models.ManyToManyField(
        Product,
        through="OrderItem",
        related_name="orders",
        blank=True,
        verbose_name="Produkty",
    )
    pick_up_day = models.CharField(
        max_length=10, choices=PICKUP_CHOICES, verbose_name="Dzień odbioru"
    )
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    is_given = models.BooleanField(default=False)  # do I need this?
    order_number = models.IntegerField(blank=True, verbose_name="Numer zamówienia")
    paid_amount = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Zapłacono", null=True, blank=True
    )

    objects = OrderManager()

    class Meta:
        verbose_name = "Zamówienie"
        verbose_name_plural = "Zamówienia"
        ordering = ["-date_created"]
        indexes = [
            models.Index(fields=["date_created"]),
        ]

    def __str__(self):
        return (
            f"Zam {self.order_number} {self.user.get_full_name() or self.user.username}"
        )

    @cached_property
    def user_fund(self):
        return get_user_fund(self.user)

    @cached_property
    def order_cost(self):
        if self.pk is None:
            return Decimal("0.00")
        total = self.orderitems.annotate(
            item_cost=F("quantity") * F("product__price")
        ).aggregate(order_cost=Sum("item_cost"))["order_cost"]

        if total is None:
            return Decimal("0.00")

        return Decimal(str(total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @cached_property
    def order_cost_with_fund(self):
        return round(self.order_cost * self.user_fund, 2)

    @cached_property
    def order_balance(self):
        return self.get_paid_amount() - self.order_cost_with_fund

    def get_paid_amount(self):
        return self.paid_amount or Decimal("0.00")

    @cached_property
    def user_balance(self):
        return self.user.userprofile.payment_balance


class OrderItem(models.Model):
    QUANTITY_CHOICES = get_quantity_choices()

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="orderitems",
        verbose_name="Zamówienie",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orderitems",
        verbose_name="Produkt",
    )
    quantity = models.DecimalField(
        max_digits=6, decimal_places=3, choices=QUANTITY_CHOICES, verbose_name="Ilość"
    )
    item_ordered_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Utworzono"
    )

    class Meta:
        verbose_name = "Produkt w zamówieniu"
        verbose_name_plural = "Produkty w zamówieniu"
        ordering = ["product"]
        indexes = [
            models.Index(fields=["order", "product"]),
        ]

    def __str__(self):
        return f"Zamówiono: {self.product}"

    @cached_property
    def item_cost(self):
        return self.quantity * self.product.price
