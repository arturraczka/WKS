# Generated by Django 4.2.7 on 2023-11-09 10:16

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0002_rename_budget_userprofile_fund"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="fund",
            field=models.DecimalField(
                blank=True,
                choices=[(Decimal("1.1"), 1.1), (Decimal("1.3"), 1.3)],
                decimal_places=1,
                default=Decimal("1.3"),
                max_digits=3,
            ),
        ),
    ]