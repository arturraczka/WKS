# Generated by Django 4.2.11 on 2024-04-05 19:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0041_alter_category_options_alter_order_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
