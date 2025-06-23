from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

ModelUser = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(ModelUser, on_delete=models.CASCADE, verbose_name="Użytkownik")
    fund = models.ForeignKey("UserProfileFund", on_delete=models.PROTECT, verbose_name="Fundusz")
    phone_number = models.PositiveIntegerField(blank=True, null=True, verbose_name="Numer telefonu")
    koop_id = models.PositiveIntegerField(null=False, unique=True, verbose_name="Koop ID")
    allow_emails = models.BooleanField(default=False, verbose_name="Zgoda na maile systemowe")
    payment_balance = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0"), verbose_name="Dług / nadpłata")

    def __str__(self):
        return f"Profil: {self.user.first_name} {self.user.last_name}"

    def apply_order_balance(self, balance_delta: Decimal):
        self.payment_balance += balance_delta
        self.save(update_fields=["payment_balance"])


class UserProfileFund(models.Model):
    value = models.DecimalField(max_digits=3, decimal_places=2, verbose_name="Wartość funduszu.", unique=True)

    def __str__(self):
        return str(self.value)
