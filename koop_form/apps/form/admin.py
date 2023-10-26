from django.contrib import admin
from apps.form.models import Producer, WeightScheme, Status, Product, Order, OrderItem, product_weight_schemes


class ProductWeightSchemeInLine(admin.TabularInline):
    model = product_weight_schemes
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    inlines = (ProductWeightSchemeInLine,)


admin.site.register(Producer)
admin.site.register(WeightScheme)
admin.site.register(Status)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
