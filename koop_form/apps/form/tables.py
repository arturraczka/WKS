import logging
from itertools import count
import django_tables2 as tables
from crispy_forms.utils import render_crispy_form

from django.core.exceptions import MultipleObjectsReturned
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.form.forms import CreateOrderItemFromProductForm
from apps.form.models import Product


logger = logging.getLogger("django.server")


class ProductTable(tables.Table):
    add_product = tables.Column(verbose_name="Add product", empty_values=())

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "producer",
            "price",
            "name",
            "add_product",
            "quantity_in_stock",
            "category",
            "description",
        )

    def __init__(self, *args, csrf_token=None, row_num=None, order, **kwargs):
        super().__init__(*args, **kwargs)
        self._csrf_token = csrf_token
        self._form_counter = count()
        self.order = order
        self.row_num = row_num
        self.current_count = next(self._form_counter)

    def render_producer(self, record, column):
        return f"{record.producer} [{record.producer.short}]"

    def render_price(self, record, column):
        return f"{record.price} zł za szt/kg"

    def render_name(self, record, column):
        if statuses := record.statuses.all():
            name_and_status = render_to_string(
                "form/components/name_and_status.html",
                {
                    "product_name": record.name,
                    "statuses": statuses,
                },
            )
            return mark_safe(name_and_status)
        return record.name[:-5]

    def render_category(self, record, column):
        if record.subcategory:
            return f"{record.category}, {record.subcategory}"
        return record.category

    def render_add_product(self, record, column):
        self.current_count = next(self._form_counter)
        row_num = self.row_num or self.current_count

        order_item_exists = any(
            oi.product_id == record.id for oi in self.order.orderitems.all()
        )

        if order_item_exists:
            try:
                order_item = self.order.orderitems.get(product=record)
            except MultipleObjectsReturned:
                order_item = self.order.orderitems.filter(product=record).first()
                error_message = f"multiple order items found for product: {record} and order: {self.order}"
                logger.error(error_message)
            form = CreateOrderItemFromProductForm(
                prefix=row_num,
                product=record,
                initial={"quantity": order_item.quantity},
            )
        else:
            form = CreateOrderItemFromProductForm(prefix=row_num, product=record)
        form_html = render_crispy_form(form)

        if order_item_exists:
            button_html = render_to_string(
                "form/components/htmx_update_button.html",
                {
                    "post_url": reverse("update-orderitem-htmx-view"),
                    "csrf_token": self._csrf_token,
                    "order_item": order_item,
                    "row_num": row_num,
                    "record": record,
                },
            )
        else:
            button_html = render_to_string(
                "form/components/htmx_add_button.html",
                {
                    "post_url": reverse("create-orderitem-htmx-view"),
                    "csrf_token": self._csrf_token,
                    "order": self.order,
                    "row_num": row_num,
                    "record": record,
                },
            )

        return mark_safe(form_html + button_html)
