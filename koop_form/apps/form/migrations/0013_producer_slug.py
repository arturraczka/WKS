# Generated by Django 4.2.5 on 2023-09-21 10:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0012_remove_order_is_archived"),
    ]

    operations = [
        migrations.AddField(
            model_name="producer",
            name="slug",
            field=models.CharField(default="slug"),
            preserve_default=False,
        ),
    ]
