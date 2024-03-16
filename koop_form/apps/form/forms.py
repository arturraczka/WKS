from crispy_forms.helper import FormHelper
from django.forms import (
    ModelForm,
    HiddenInput,
    Form,
    CharField,
    BaseModelFormSet,
    ModelChoiceField,
)

from apps.form.models import OrderItem, Order


class CreateOrderForm(ModelForm):
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
            "quantity": "szt/kg",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["order"].widget = HiddenInput()
        self.fields["product"].widget = HiddenInput()


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        # self.helper.tag=None
        # self.helper.wrapper_class=None

