from django.contrib import admin
from apps.form.models import Product
from apps.form.services import alter_product_stock, reduce_product_stock
from apps.supply.models import (
    Supply,
    SupplyItem,
)


class SupplyAdmin(admin.ModelAdmin):
    list_filter = ["producer__short", "date_created"]
    list_display = ["producer_short", "created_by", "date_created"]
    search_fields = ["producer__short"]

    @admin.display(description="Producer short")
    def producer_short(self, obj):
        return f"{obj.producer.short}"

    @admin.display(description="Created by")
    def created_by(self, obj):
        return f"{obj.user.last_name}"


class SupplyItemAdmin(admin.ModelAdmin):
    raw_id_fields = ("product",)
    list_filter = ["product__producer__short", "date_created"]
    list_display = ["producer_short", "product_name", "quantity", "date_created"]
    search_fields = ["product__name"]

    @admin.display(description="Product name")
    def product_name(self, obj):
        return f"{obj.product.name}"

    @admin.display(description="Producer short")
    def producer_short(self, obj):
        return f"{obj.product.producer.short}"

    def save_model(self, request, obj, form, change):
        if change:
            alter_product_stock(Product, obj.product.id, obj.quantity, obj.id, SupplyItem, negative=True)
        else:
            reduce_product_stock(Product, obj.product.id, obj.quantity, negative=True)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        reduce_product_stock(Product, obj.product.id, obj.quantity)
        super().delete_model(request, obj)


admin.site.register(Supply, SupplyAdmin)
admin.site.register(SupplyItem, SupplyItemAdmin)
