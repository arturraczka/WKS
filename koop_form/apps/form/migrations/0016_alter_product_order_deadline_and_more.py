# Generated by Django 4.2.5 on 2023-09-26 10:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0015_alter_producer_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="order_deadline",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="quantity_delivered_this_week",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=0, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="quantity_in_stock",
            field=models.DecimalField(
                blank=True, decimal_places=3, max_digits=6, null=True
            ),
        ),
    ]
