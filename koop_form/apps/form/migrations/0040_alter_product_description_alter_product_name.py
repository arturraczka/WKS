# Generated by Django 4.2.7 on 2024-03-13 11:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0039_rename_new_category_product_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(max_length=100),
        ),
    ]