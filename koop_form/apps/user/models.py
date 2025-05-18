from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

ModelUser = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(ModelUser, on_delete=models.CASCADE)
    fund = models.ForeignKey("UserProfileFund", on_delete=models.PROTECT, verbose_name="Fundusz")
    phone_number = models.PositiveIntegerField(blank=True, null=True)
    koop_id = models.PositiveIntegerField(null=False, unique=True)
    allow_emails = models.BooleanField(default=False)

    def __str__(self):
        return f"Profil: {self.user.first_name} {self.user.last_name}"


class UserProfileFund(models.Model):
    value = models.DecimalField(max_digits=3, decimal_places=2, verbose_name="Wartość funduszu.", unique=True)

    def __str__(self):
        return str(self.value)
