import logging

from django.forms import (
    ModelForm,
    HiddenInput,
    Form,
    CharField,
    BaseModelFormSet,
    ModelChoiceField,
    BaseInlineFormSet,
    widgets,
)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from apps.form.models import OrderItem, Order, Product
from apps.form.services import (
    calculate_order_number,
    reduce_product_stock,
    alter_product_stock,
)


logger = logging.getLogger("django.server")


class DeleteOrderForm(ModelForm):
    form_html = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = True
        self.helper.form_class = ""
        self.helper.tag = None
        self.helper.wrapper_class = None
        self.helper.add_input(Submit("submit", "Usuń"))

    class Meta:
        model = Order
        fields = []


class CreateOrderForm(ModelForm):
    def __init__(self, update=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update = update
        self.helper = FormHelper(self)
        self.helper.include_media = True
        self.helper.form_class = ""
        self.helper.tag = None
        self.helper.wrapper_class = None
        if self.update:
            self.helper.add_input(Submit("submit", "Zmień dzień odbioru"))
        else:
            self.helper.add_input(Submit("submit", "Utwórz zamówienie"))

    class Meta:
        model = Order
        fields = ["pick_up_day"]
        labels = {
            "pick_up_day": "Wybierz dzień odbioru:",
        }


class CreateOrderItemForm(ModelForm):
    order = ModelChoiceField(required=False, queryset=Order.objects.all())

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "order"]
        labels = {
            "quantity": "",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["order"].widget = HiddenInput()
        self.fields["product"].widget = HiddenInput()
        self.helper = FormHelper(self)
        self.helper.include_media = True
        self.helper.tag = None
        self.helper.wrapper_class = None

        # # this makes formset work:
        self.helper.form_tag = False
        # self.helper.add_input(Submit("submit", "Dodaj"))
        # # wywalenie add_input i dodanie submitu do templatki


class CreateOrderItemFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = OrderItem.objects.none()


class UpdateOrderItemForm(ModelForm):
    class Meta:
        model = OrderItem
        fields = "__all__"
        labels = {
            "quantity": "szt/kg",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].widget = HiddenInput()
        self.fields["order"].widget = HiddenInput()


class UpdateOrderItemFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SearchForm(Form):
    search_query = CharField(
        label="Wyszukaj po nazwie produktu. Minimum 3 litery, wielkość liter nie ma znaczenia, używaj polskich znaków.",
        max_length=25,
        min_length=3,
        required=False,
    )


class OrderInlineFormset(BaseInlineFormSet):
    def get_queryset(self):
        return Order.objects.none()

    def save_new(self, form, commit=True):
        instance = super().save_new(form, commit=False)
        instance.order_number = calculate_order_number(Order)
        if commit:
            instance.save()
        return instance


class OrderItemFormInline(ModelForm):
    class Meta:
        model = OrderItem
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].disabled = True
        instance = getattr(self.instance, "product", None)
        instance_representation = str(instance) if instance else ""
        self.fields["product"].widget.choices = [
            (instance_representation, instance_representation),
        ]


class OrderItemInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = OrderItemFormInline

    def save_existing(self, form, instance, commit=True):
        alter_product_stock(
            Product, instance.product.id, instance.quantity, instance.id, OrderItem
        )
        super().save_existing(form, instance, commit=commit)

    def delete_existing(self, obj, commit=True):
        if commit:
            reduce_product_stock(Product, obj.product.id, obj.quantity, negative=True)
            obj.delete()


class OrderItemEmptyInlineFormset(BaseInlineFormSet):
    def get_queryset(self):
        return OrderItem.objects.none()

    def save_new(self, form, commit=True):
        instance = super().save_new(form, commit=False)
        logger.info(instance)
        reduce_product_stock(Product, instance.product.id, instance.quantity)
        return super().save_new(form, commit=commit)
