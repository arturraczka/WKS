# Generated by Django 4.2.7 on 2024-01-07 16:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("form", "0035_remove_supplyitem_product_remove_supplyitem_supply_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Supply",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                (
                    "producer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supplies",
                        to="form.producer",
                    ),
                ),
            ],
            options={
                "ordering": ["producer__short", "-date_created"],
            },
        ),
        migrations.CreateModel(
            name="SupplyItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=6)),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supplyitems",
                        to="form.product",
                    ),
                ),
                (
                    "supply",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supplyitems",
                        to="supply.supply",
                    ),
                ),
            ],
            options={
                "ordering": ["supply", "-date_created"],
            },
        ),
        migrations.AddField(
            model_name="supply",
            name="product",
            field=models.ManyToManyField(
                blank=True,
                related_name="supplies",
                through="supply.SupplyItem",
                to="form.product",
            ),
        ),
        migrations.AddField(
            model_name="supply",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="supplies",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="supply",
            index=models.Index(
                fields=["date_created"], name="supply_supp_date_cr_71a060_idx"
            ),
        ),
    ]
