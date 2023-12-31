# Generated by Django 4.2.5 on 2023-09-13 15:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0007_alter_order_products_alter_orderitem_product"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="products",
            field=models.ManyToManyField(
                blank=True,
                related_name="orders",
                through="form.OrderItem",
                to="form.product",
            ),
        ),
    ]
