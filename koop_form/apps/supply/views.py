import logging

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.forms import modelformset_factory
from django.views.generic import (
    CreateView,
    FormView,
)

from apps.form.models import Producer, Product
from apps.supply.models import Supply, SupplyItem
from apps.supply.forms import (
    CreateSupplyForm,
    CreateSupplyItemFormSet,
    CreateSupplyItemForm,
    UpdateSupplyItemFormSet,
    UpdateSupplyItemForm,
)
from apps.form.services import (
    staff_check,
)


logger = logging.getLogger("django.server")


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyCreateView(SuccessMessageMixin, CreateView):
    model = Supply
    template_name = "report/supply_create.html"
    form_class = CreateSupplyForm
    success_message = "Dostawa została utworzona. Dodaj produkty."

    def form_valid(self, form):
        # TODO
        # if validate_order_exists(self.request):
        #     return self.form_invalid(form)
        # mogę zrobić walidację, żeby nie dało się zrobić dwóch dostaw tego samego producenta w jednym tygodniu

        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyProductsFormView(FormView):
    model = SupplyItem
    template_name = "report/supply_products_form.html"
    form_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.supply = None
        self.products = None
        self.producer = None

    def get_success_url(self):
        return self.request.path

    def get_producer_object(self):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])

    def get_products_query(self):
        self.products = (
            Product.objects.filter(producer=self.producer).filter(is_active=True)
            # .only("id")
        )

    def get_producer_products(self):
        self.get_producer_object()
        self.get_products_query()

    def get_form_class(self):
        self.get_producer_products()
        supply_item_formset = modelformset_factory(
            SupplyItem,
            form=CreateSupplyItemForm,
            formset=CreateSupplyItemFormSet,
            extra=self.products.count(),
        )
        return supply_item_formset

    def get_initial(self):
        supply_qs = Supply.objects.filter(producer=self.producer).order_by(
            "-date_created"
        )
        self.supply = get_list_or_404(supply_qs)[0]
        return [
            {"product": product.id, "supply": self.supply} for product in self.products
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = self.products
        context["producer"] = self.producer
        supply_items = SupplyItem.objects.filter(supply=self.supply)
        context["supply_items"] = supply_items
        return context

    def form_valid(self, form):
        formset = form.save(commit=False)
        for instance in formset:
            if instance.quantity == 0:
                pass
            elif instance.quantity is None:
                pass
            else:
                if False:
                    pass
                # if not perform_create_orderitem_validations(
                #     instance, self.request, Order, Product
                # ):
                #     return self.form_invalid(form)
                else:
                    # instance.supply = self.supply.id
                    instance.save()
                    messages.success(
                        self.request,
                        f"{instance.product.name}: Produkt został uwzględniony w dostawie.",
                    )
        return super().form_valid(form)


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyUpdateFormView(FormView):
    model = SupplyItem
    form_class = None
    template_name = "report/supply_update_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.supply_items = None
        self.products = None
        self.supply = None
        self.producer = None

    def get_success_url(self):
        return self.request.path

    # TODO zmień kurwa nazwę tej metody
    def get_shit_done(self):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        self.supply = (
            Supply.objects.filter(producer=self.producer)
            .order_by("-date_created")
            .first()
        )
        self.supply_items = (
            SupplyItem.objects.filter(supply=self.supply)
            .select_related("product")
            .only("product_id", "quantity", "product__name")
            .order_by("product__name")
        )

    def get_form_class(self):
        self.get_shit_done()
        supply_item_formset = modelformset_factory(
            SupplyItem,
            form=UpdateSupplyItemForm,
            formset=UpdateSupplyItemFormSet,
            edit_only=True,
            extra=0,
        )
        return supply_item_formset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["queryset"] = self.supply_items
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.products = Product.objects.filter(supplies=self.supply).only("id", "name")
        context["supply"] = self.supply
        context["producer"] = self.producer
        context["products"] = self.products

        return context

    def form_valid(self, form):
        formset = form.save(commit=False)
        for instance in formset:
            # if not perform_update_orderitem_validations(instance, self.request):
            #     return self.form_invalid(form)
            instance.save()
            messages.success(
                self.request,
                f"{instance.product.name}: Dostawa została zaktualizowana.",
            )
        return super().form_valid(form)
