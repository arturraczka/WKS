from django.forms import (
    ModelForm,
    HiddenInput,
    BaseModelFormSet,
    ModelChoiceField,
)

from apps.supply.models import Supply, SupplyItem


class CreateSupplyForm(ModelForm):
    class Meta:
        model = Supply
        fields = ["producer"]
        labels = {
            "producer": "Wybierz producenta:",
        }

    def __init__(self, *args, **kwargs):
        producers = kwargs.pop('producers')
        super().__init__(*args, **kwargs)
        self.fields['producer'].queryset = producers


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
