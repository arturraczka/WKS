# Generated by Django 4.2.7 on 2023-11-03 09:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("form", "0022_productweightscheme_alter_product_weight_schemes"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="orderitem",
            options={"ordering": ["product"]},
        ),
        migrations.RenameField(
            model_name="product",
            old_name="is_visible",
            new_name="is_active",
        ),
        migrations.AddField(
            model_name="producer",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="product_weight_schemes",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="form.product"
            ),
        ),
        migrations.AlterField(
            model_name="product_weight_schemes",
            name="weightscheme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="form.weightscheme"
            ),
        ),
        migrations.AlterModelTable(
            name="product_weight_schemes",
            table=None,
        ),
    ]
