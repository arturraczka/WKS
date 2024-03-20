from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import (
    ModelForm,
    HiddenInput,
    BaseModelFormSet,
    ModelChoiceField,
)

from apps.supply.models import Supply, SupplyItem


class DeleteSupplyForm(ModelForm):
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
        model = Supply
        fields = []


class CreateSupplyForm(ModelForm):
    class Meta:
        model = Supply
        fields = ["producer"]
        labels = {
            "producer": "Wybierz producenta:",
        }

    def __init__(self, *args, **kwargs):
        producers = kwargs.pop("producers")
        super().__init__(*args, **kwargs)
        self.fields["producer"].queryset = producers


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
