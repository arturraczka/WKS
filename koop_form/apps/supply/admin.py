from django.contrib import admin

# from import_export.admin import ImportExportModelAdmin
# from import_export import resources, fields, widgets

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


admin.site.register(Supply, SupplyAdmin)
admin.site.register(SupplyItem, SupplyItemAdmin)
