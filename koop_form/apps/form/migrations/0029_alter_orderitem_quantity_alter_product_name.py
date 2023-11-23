# Generated by Django 4.2.7 on 2023-11-23 07:47

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0028_alter_orderitem_quantity"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="quantity",
            field=models.DecimalField(
                choices=[
                    (Decimal("0.000"), "0"),
                    (Decimal("10.000"), "10"),
                    (Decimal("0.010"), "0.01"),
                    (Decimal("0.100"), "0.1"),
                    (Decimal("1.000"), "1"),
                    (Decimal("1.500"), "1.5"),
                    (Decimal("0.020"), "0.02"),
                    (Decimal("0.200"), "0.2"),
                    (Decimal("2.000"), "2"),
                    (Decimal("2.500"), "2.5"),
                    (Decimal("0.030"), "0.03"),
                    (Decimal("0.300"), "0.3"),
                    (Decimal("3.000"), "3"),
                    (Decimal("3.500"), "3.5"),
                    (Decimal("0.040"), "0.04"),
                    (Decimal("0.400"), "0.4"),
                    (Decimal("4.000"), "4"),
                    (Decimal("4.500"), "4.5"),
                    (Decimal("0.050"), "0.05"),
                    (Decimal("0.500"), "0.5"),
                    (Decimal("5.000"), "5"),
                    (Decimal("5.500"), "5.5"),
                    (Decimal("0.060"), "0.06"),
                    (Decimal("0.600"), "0.6"),
                    (Decimal("6.000"), "6"),
                    (Decimal("6.500"), "6.5"),
                    (Decimal("0.070"), "0.07"),
                    (Decimal("0.700"), "0.7"),
                    (Decimal("7.000"), "7"),
                    (Decimal("7.500"), "7.5"),
                    (Decimal("0.080"), "0.08"),
                    (Decimal("0.800"), "0.8"),
                    (Decimal("8.000"), "8"),
                    (Decimal("8.500"), "8.5"),
                    (Decimal("0.090"), "0.09"),
                    (Decimal("0.900"), "0.9"),
                    (Decimal("9.000"), "9"),
                    (Decimal("9.500"), "9.5"),
                ],
                decimal_places=3,
                max_digits=6,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(),
        ),
    ]
