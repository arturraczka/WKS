from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

ModelUser = get_user_model()


class UserProfile(models.Model):
    FUND_CHOICES = [
        (Decimal("1.1"), 1.1),
        (Decimal("1.3"), 1.3),
    ]
    user = models.OneToOneField(ModelUser, on_delete=models.CASCADE)
    fund = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        choices=FUND_CHOICES,
        blank=True,
        default=Decimal("1.3"),
    )
    phone_number = models.PositiveIntegerField(blank=True, null=True)
    koop_id = models.PositiveIntegerField(null=False, unique=True)

    def __str__(self):
        return f"profile: {self.user.username}"
