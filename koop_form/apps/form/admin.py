from django.contrib import admin, messages

from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets

from apps.form.forms import OrderInlineFormset, OrderItemInlineFormset, OrderItemEmptyInlineFormset
from apps.form.models import (
    Producer,
    WeightScheme,
    Status,
    Product,
    Order,
    OrderItem,
    product_weight_schemes,
    Category,
)
from apps.form.services import (
    calculate_previous_weekday,
    reduce_product_stock,
    alter_product_stock, calculate_order_number,
)


class ProductWeightSchemeInLine(admin.TabularInline):
    model = product_weight_schemes
    extra = 1


class OrderItemInLine(admin.TabularInline):
    model = OrderItem
    extra = 0
    verbose_name_plural = "Edytuj ilość lub usuń produkt z zamówienia:"
    verbose_name = "Edytuj ilość lub usuń produkt z zamówienia:"
    formset = OrderItemInlineFormset

    def has_add_permission(self, request, obj):
        return False


class OrderItemEmptyInLine(admin.TabularInline):
    model = OrderItem
    extra = 0

    verbose_name_plural = "Dodaj nowy produkt do zamówienia:"
    verbose_name = "Dodaj nowy produkt do zamówienia:"
    formset = OrderItemEmptyInlineFormset


class OrderInLine(admin.StackedInline):
    model = Order
    can_delete = False
    verbose_name_plural = "Zamówienia:"
    verbose_name = "Zamówienie:"
    extra = 1
    fields = ["pick_up_day"]
    formset = OrderInlineFormset


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


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = [
        "name",
        "is_active",
        "price",
        "quantity_in_stock",
    ]


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
    inlines = [ProductInline]

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
                reduce_product_stock(Product, item.product.id, item.quantity, negative=True)
                item.delete()

    def not_arrived_deletes_related_orderitems(self, instance):
        """If Producer.not_arrived equal True, then proceeds to remove """
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
            "is_stocked",
        )


class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [ProductResource]
    list_filter = ["is_stocked", "is_active", "producer__name"]
    inlines = (ProductWeightSchemeInLine,)
    list_display = [
        "name",
        "price",
        "producer",
        "category",
        "quantity_in_stock",
        "is_active",
    ]
    search_fields = [
        "name",
    ]


class OrderAdmin(admin.ModelAdmin):
    list_select_related = True
    fields = ["user", "pick_up_day", "order_number", "order_cost_with_fund", "user_balance", "paid_amount", "order_payment_balance"]
    list_filter = ["date_created", "order_number", "user__last_name"]
    list_display = ["user_last_name", "order_number", "date_created"]
    search_fields = [
        "user__last_name",
    ]
    inlines = (OrderItemEmptyInLine, OrderItemInLine,)
    readonly_fields = ["order_cost_with_fund", "user_balance", "order_payment_balance", "order_number"]

    @admin.display(description="User last name")
    def user_last_name(self, obj):
        return f"{obj.user.last_name}"

    def delete_model(self, request, obj):
        for item in obj.orderitems.all():
            reduce_product_stock(Product, item.product.id, item.quantity, negative=True)
        obj.delete()

    def delete_queryset(self, request, queryset):
        for order in queryset:
            for item in order.orderitems.all():
                reduce_product_stock(Product, item.product.id, item.quantity, negative=True)
        queryset.delete()

    @staticmethod
    def update_user_balance(order):
        try:
            db_order = Order.objects.get(id=order.id)
            db_paid = db_order.paid_amount
            db_balance = db_order.order_balance
        except Order.DoesNotExist:
            db_paid = None
            db_balance = -order.order_cost_with_fund

        new_paid = order.paid_amount
        new_balance = order.order_balance

        payments_stay_the_same = db_paid == new_paid
        if payments_stay_the_same:
            return

        new_payment_is_none = new_paid is None
        if new_payment_is_none:
            order.user.userprofile.apply_order_balance(-db_balance)
            return

        old_payment_is_none = db_paid is None
        if old_payment_is_none:
            order.user.userprofile.apply_order_balance(new_balance)
            return

        balance_delta = new_balance - db_balance
        order.user.userprofile.apply_order_balance(balance_delta)

    def save_model(self, request, obj, form, change):
        if change:
            self.update_user_balance(order=obj)
        if not change:
            if obj.paid_amount is not None:
                obj.paid_amount = None
                self.message_user(
                    request,
                    "Nie zapisano płatności podczas tworzenia zamówienia. Płatność możesz zapisać jedynie aktualizując zamówienie.",
                    messages.ERROR,
                )
            obj.order_number = calculate_order_number(Order)
        super().save_model(request, obj, form, change)

    def order_cost_with_fund(self, obj):
        return f"{obj.order_cost_with_fund:.2f} zł"

    order_cost_with_fund.short_description = "Kwota zamówienia z funduszem"

    def order_payment_balance(self, obj):
        return f"{obj.order_balance:.2f} zł"

    order_payment_balance.short_description = "Dług / nadpłata zamówienia"

    def user_balance(self, obj):
        return f"{obj.user_balance:.2f} zł"

    user_balance.short_description = "Dług / nadpłata koopowicza"


class OrderItemAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_select_related = True
    raw_id_fields = (
        "product",
        "order",
    )
    list_filter = [
        "order__date_created",
        "order__order_number",
        "order__user__last_name",
        "product__producer",
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
            alter_product_stock(
                Product, obj.product.id, obj.quantity, obj.id, OrderItem
            )
        else:
            reduce_product_stock(Product, obj.product.id, obj.quantity)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        reduce_product_stock(Product, obj.product.id, obj.quantity, negative=True)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for item in queryset:
            reduce_product_stock(Product, item.product.id, item.quantity, negative=True)
        queryset.delete()


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "id"]


admin.site.register(Producer, ProducerAdmin)
admin.site.register(WeightScheme)
admin.site.register(Status)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
