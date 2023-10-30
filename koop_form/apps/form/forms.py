from django.forms import ModelForm, HiddenInput
from apps.form.models import OrderItem, Order
from django.forms import BaseModelFormSet


class CreateOrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ["pick_up_day"]


class CreateOrderItemForm(ModelForm):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]
        labels = {
            "quantity": "sztuk/waga(kg)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].widget = HiddenInput()


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
