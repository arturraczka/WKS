# Generated by Django 4.2.7 on 2024-01-07 16:09

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0034_producer_manager_email_producer_manager_name_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="supplyitem",
            name="product",
        ),
        migrations.RemoveField(
            model_name="supplyitem",
            name="supply",
        ),
        migrations.AlterModelOptions(
            name="product",
            options={"ordering": ["name"]},
        ),
        migrations.DeleteModel(
            name="Supply",
        ),
        migrations.DeleteModel(
            name="SupplyItem",
        ),
    ]
