from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets

from apps.form.models import (
    Producer,
    WeightScheme,
    Status,
    Product,
    Order,
    OrderItem,
    product_weight_schemes,
    Supply,
    SupplyItem,
)


class ProductWeightSchemeInLine(admin.TabularInline):
    model = product_weight_schemes
    extra = 1


class ProducerResource(resources.ModelResource):
    class Meta:
        model = Producer
        import_id_fields = ("id",)
        fields = (
            "id",
            "name",
            "short",
            "manager_name",
            "manager_email",
            "manager_phone",
            "description",
        )


class ProducerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [ProducerResource]
    list_display = ["name", "short", "is_active"]


class ProductResource(resources.ModelResource):
    weight_schemes = fields.Field(
        column_name='weight_schemes',
        attribute='weight_schemes',
        widget=widgets.ManyToManyWidget(WeightScheme, field='quantity', separator='|')
    )

    class Meta:
        model = Product
        import_id_fields = ("id",)
        fields = (
            "id",
            "producer",
            "name",
            "description",
            "price",
            "category",
            "subcategory",
            "unit",
            "info",
        )


class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [ProductResource]
    list_filter = ["producer__name"]
    inlines = (ProductWeightSchemeInLine,)
    list_display = ["name", "producer", "is_active"]
    search_fields = [
        "name",
    ]


class OrderAdmin(admin.ModelAdmin):
    list_filter = ["user__last_name", "date_created"]
    list_display = ["user_last_name", "order_number", "date_created"]
    search_fields = [
        "user__last_name",
    ]

    @admin.display(description="User last name")
    def user_last_name(self, obj):
        return f"{obj.user.last_name}"


class OrderItemAdmin(admin.ModelAdmin):
    raw_id_fields = ('product',)
    list_filter = [
        "order__user__last_name",
        "order__date_created",
        "order__order_number",
    ]
    list_display = [
        "producer_short",
        "product_name",
        "order_user",
        "order_number",
        "quantity",
        "item_ordered_date",
    ]
    search_fields = [
        "product__name",
    ]

    @admin.display(description="Order number")
    def order_number(self, obj):
        return f"{obj.order.order_number}"

    @admin.display(description="Order user")
    def order_user(self, obj):
        return f"{obj.order.user.last_name}"

    @admin.display(description="Product name")
    def product_name(self, obj):
        return f"{obj.product.name}"

    @admin.display(description="Producer short")
    def producer_short(self, obj):
        return f"{obj.product.producer.short}"


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
    raw_id_fields = ('product',)
    list_filter = ["product__producer__short", "date_created"]
    list_display = ["producer_short", "product_name", "quantity", "date_created"]
    search_fields = ["product__name"]

    @admin.display(description="Product name")
    def product_name(self, obj):
        return f"{obj.product.name}"

    @admin.display(description="Producer short")
    def producer_short(self, obj):
        return f"{obj.product.producer.short}"


admin.site.register(Producer, ProducerAdmin)
admin.site.register(WeightScheme)
admin.site.register(Status)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Supply, SupplyAdmin)
admin.site.register(SupplyItem, SupplyItemAdmin)
