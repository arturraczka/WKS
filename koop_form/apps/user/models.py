from django.db import models
from django.contrib.auth import get_user_model

ModelUser = get_user_model()


class UserProfile(models.Model):
    BUDGET_CHOICES = [
        (1.1, 1.1),
        (1.3, 1.3),
    ]
    user = models.OneToOneField(ModelUser, on_delete=models.CASCADE)
    budget = models.DecimalField(max_digits=3, decimal_places=1, choices=BUDGET_CHOICES, blank=True, default=1.3)
    phone_number = models.PositiveIntegerField(blank=True, null=True)
