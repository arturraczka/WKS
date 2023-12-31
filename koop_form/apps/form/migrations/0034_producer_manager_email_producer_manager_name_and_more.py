# Generated by Django 4.2.7 on 2023-12-18 18:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0033_product_category_product_info_product_subcategory_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="producer",
            name="manager_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name="producer",
            name="manager_name",
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="producer",
            name="manager_phone",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
