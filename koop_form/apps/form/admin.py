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
    product_weight_schemes, Category,
)
from apps.form.services import calculate_previous_weekday, reduce_product_stock, alter_product_stock


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
    list_display = [
        "name",
        "short",
        "is_active",
        "manager_name",
        "manager_email",
        "manager_phone",
    ]
    list_editable = ["is_active"]

    def set_order_deadline_to_related_products(self, instance):
        products = instance.products.all()
        for product in products:
            product.order_deadline = instance.order_deadline
            product.save()

    def perform_delete(self, instance):
        products = instance.products.all()
        for product in products:
            orderitems = OrderItem.objects.filter(
                product=product, item_ordered_date__gt=calculate_previous_weekday()
            )
            for item in orderitems:
                item.delete()

    def not_arrived_deletes_related_orderitems(self, instance):
        if instance.not_arrived:
            self.perform_delete(instance)
            instance.not_arrived = False

    def save_model(self, request, obj, form, change):
        self.not_arrived_deletes_related_orderitems(obj)
        super().save_model(request, obj, form, change)
        self.set_order_deadline_to_related_products(obj)


class ProductResource(resources.ModelResource):
    weight_schemes = fields.Field(
        column_name="weight_schemes",
        attribute="weight_schemes",
        widget=widgets.ManyToManyWidget(WeightScheme, field="quantity", separator="|"),
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
            "quantity_in_stock",
            "is_active",
        )


class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [ProductResource]
    list_filter = ["producer__name"]
    inlines = (ProductWeightSchemeInLine,)
    list_display = ["name", "price", "producer", "category", "quantity_in_stock", "is_active"]
    list_editable = ["price", "is_active", "quantity_in_stock"]
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
    raw_id_fields = (
        "product",
        "order",
    )
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
    list_editable = ["quantity"]
    search_fields = [
        "product__name",
        "order__user__last_name",
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

    def save_model(self, request, obj, form, change):
        if change:
            alter_product_stock(Product, obj.product.id, obj.quantity, obj.id, OrderItem)
        else:
            reduce_product_stock(Product, obj.product.id, obj.quantity)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        reduce_product_stock(Product, obj.product.id, obj.quantity, negative=True)
        super().delete_model(request, obj)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "id"]


admin.site.register(Producer, ProducerAdmin)
admin.site.register(WeightScheme)
admin.site.register(Status)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
