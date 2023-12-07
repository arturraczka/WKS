from django.forms import (
    ModelForm,
    HiddenInput,
    Form,
    CharField,
    BaseModelFormSet,
    ModelChoiceField,
)

from apps.form.models import OrderItem, Order, Supply, SupplyItem


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
            "quantity": "sztuk/waga(kg)",
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
            "quantity": "sztuk/waga(kg)",
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


class CreateSupplyForm(ModelForm):
    class Meta:
        model = Supply
        fields = ["producer"]
        labels = {
            "producer": "Wybierz producenta:",
        }


class CreateSupplyItemForm(ModelForm):
    supply = ModelChoiceField(required=False, queryset=Supply.objects.all())

    class Meta:
        model = SupplyItem
        fields = ["product", "quantity", "supply"]
        labels = {
            "quantity": "sztuk/waga(kg)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supply"].widget = HiddenInput()
        self.fields["product"].widget = HiddenInput()


class CreateSupplyItemFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = SupplyItem.objects.none()


class UpdateSupplyItemForm(ModelForm):
    class Meta:
        model = SupplyItem
        fields = "__all__"
        labels = {
            "quantity": "sztuk/waga(kg)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].widget = HiddenInput()
        self.fields["supply"].widget = HiddenInput()


class UpdateSupplyItemFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
