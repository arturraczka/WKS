from django.forms import ModelForm, HiddenInput, forms, Select
from apps.form.models import OrderItem, Order
from django.forms import BaseModelFormSet, ChoiceField


class CreateOrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ["pick_up_day"]
        labels = {
            'pick_up_day': 'Wybierz dzień odbioru:',
        }


CHOICES = [
    (0, 0),
    (1, 1),
]


class CreateOrderItemForm(ModelForm):
    quantity = ChoiceField(
        widget=Select(),
    )

    class Meta:
        model = OrderItem
        fields = ["product"]
        labels = {
            "quantity": "sztuk/waga(kg)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].widget = HiddenInput()
        # self.fields["quantity"].widget = Select(choices=CHOICES)


class CreateOrderItemFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = OrderItem.objects.none()

    # def save_new(self, form, commit=True):
    #     return form.save(commit=commit)


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
        # self.queryset = OrderItem.objects.none()

    # def save_new(self, form, commit=True):
    #     return form.save(commit=commit)


# OrderItemFormSet = modelformset_factory(
#     OrderItem,
#     form=CreateOrderItemForm,
#     formset=CreateOrderItemFormSet,
# )
