# Generated by Django 4.2.7 on 2023-11-09 07:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0025_alter_order_pick_up_day"),
    ]

    operations = [
        migrations.AddField(
            model_name="producer",
            name="not_arrived",
            field=models.BooleanField(blank=True, default=False),
        ),
    ]