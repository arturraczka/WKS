from django.contrib import admin

from apps.form.models import (
    Producer,
    WeightScheme,
    Status,
    Product,
    Order,
    OrderItem,
    product_weight_schemes,
)


class ProductWeightSchemeInLine(admin.TabularInline):
    model = product_weight_schemes
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_filter = ["producer__name"]
    inlines = (ProductWeightSchemeInLine,)


class OrderAdmin(admin.ModelAdmin):
    list_filter = ["user__last_name", "date_created"]


class OrderItemAdmin(admin.ModelAdmin):
    list_filter = ["order__user__last_name", "order__date_created"]


admin.site.register(Producer)
admin.site.register(WeightScheme)
admin.site.register(Status)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
