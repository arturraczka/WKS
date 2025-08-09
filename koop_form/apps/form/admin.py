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
    reduce_product_stock,
    alter_product_stock,
    calculate_order_number,
    display_as_zloty,
)
from apps.form.helpers import koop_default_interval_start


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
                product=product, item_ordered_date__gt=koop_default_interval_start()
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
    fields = ["user", "pick_up_day", "order_number", "user_fund", "order_cost", "order_cost_with_fund", "user_balance", "user_and_order_balance", "paid_amount"]
    list_filter = ["date_created", "order_number", "user__last_name"]
    list_display = ["__str__", "order_number", "order_cost_with_fund", "user_balance", "is_settled", "paid_amount", "date_created"]
    search_fields = [
        "user__last_name",
        "user__first_name",
        "user__email",
        "user__username",
    ]
    inlines = (OrderItemEmptyInLine, OrderItemInLine,)
    readonly_fields = ["order_cost_with_fund", "user_balance", "order_number", "user_fund", "order_cost", "user_and_order_balance"]
    autocomplete_fields = ["user"]

    @admin.display(description="czy rozliczone?")
    def is_settled(self, obj):
        if obj.paid_amount is not None:
            return "Tak"
        return "-"

    @admin.display(description="Fundusz")
    def user_fund(self, obj):
        return obj.user_fund

    @admin.display(description="Kwota zamówienia bez funduszu")
    def order_cost(self, obj):
        return display_as_zloty(obj.order_cost)

    @admin.display(description="DO ZAPŁATY. Wartość zamówienia + dług / nadpłata koopowicza")
    def user_and_order_balance(self, obj):
        value_to_pay = -obj.user_balance
        if obj.paid_amount is None:
            value_to_pay -= obj.order_balance
        return display_as_zloty(value_to_pay)

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
        db_order = Order.objects.get(id=order.id)
        old_payment = db_order.paid_amount
        old_balance = db_order.order_balance

        new_payment = order.paid_amount
        new_balance = order.order_balance

        # po zmianie logiki tak, że nie można edytować zamówienia te wszystkie warunki są niepotrzebne
        # dlatego że jedyna możliwa zmiana paid_amount to z None na not None czyli warunek old_payment is None
        # zablokowanie edycji zamówienia handlowane jest w OrderAdminRedirectView
        if old_payment == new_payment:
            return
        elif new_payment is None:
            balance_to_apply = -old_balance
        elif old_payment is None:
            balance_to_apply = new_balance
        else:
            balance_to_apply = new_balance - old_balance
        order.user.userprofile.apply_order_balance(balance_to_apply)

    # TODO TEST
    def save_model(self, request, obj, form, change):
        if change:
            self.update_user_balance(order=obj)
        else:
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
        return display_as_zloty(obj.order_cost_with_fund)

    order_cost_with_fund.short_description = "Kwota zamówienia z funduszem"

    def user_balance(self, obj):
        return display_as_zloty(obj.user_balance)

    user_balance.short_description = "Dług / nadpłata koopowicza"

    def has_change_permission(self, request, obj=None):
        if obj and obj.paid_amount is not None:
            return False
        return True


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
