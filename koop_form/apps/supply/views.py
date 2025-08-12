import logging

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.forms import modelformset_factory
from django.views.generic import (
    CreateView,
    FormView,
    TemplateView,
    DeleteView,
)

from apps.form.models import Producer, Product
from apps.form.validations import validate_supply_exists, validate_supplyitem_exists
from apps.supply.models import Supply, SupplyItem
from apps.supply.forms import (
    CreateSupplyForm,
    CreateSupplyItemFormSet,
    CreateSupplyItemForm,
    UpdateSupplyItemFormSet,
    UpdateSupplyItemForm, DeleteSupplyForm,
)
from apps.form.services import (
    staff_check,
    alter_product_stock,
    reduce_product_stock,
    filter_products_with_ordered_quantity,
)
from apps.form.helpers import calculate_previous_weekday

logger = logging.getLogger("django.server")


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyCreateView(SuccessMessageMixin, CreateView):
    model = Supply
    template_name = "supply/supply_create.html"
    form_class = CreateSupplyForm
    success_message = "Dostawa została utworzona. Dodaj produkty."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["producers"] = Producer.objects.filter(is_active=True)
        return kwargs

    def form_valid(self, form):
        if validate_supply_exists(Supply, form.instance.producer):
            messages.warning(
                self.request,
                f"{form.instance.producer}: Ten producent ma już dostawę na ten tydzień.",
            )
            return self.form_invalid(form)
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyProductsFormView(FormView):
    model = SupplyItem
    template_name = "supply/supply_products_form.html"
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
                if validate_supplyitem_exists(instance.product, SupplyItem):
                    messages.warning(
                        self.request,
                        f"{instance.product.name}: Już dodałaś/eś ten produkt do dostawy.",
                    )

                else:
                    reduce_product_stock(
                        Product, instance.product.id, instance.quantity, negative=True
                    )
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
    template_name = "supply/supply_update_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.supply_items = None
        self.products = None
        self.supply = None
        self.producer = None

    def get_success_url(self):
        return self.request.path

    def get_producer_supply_and_items(self):
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
        self.get_producer_supply_and_items()
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
            if instance.quantity == 0:
                supplyitem_db = SupplyItem.objects.get(id=instance.id)
                reduce_product_stock(
                    Product, supplyitem_db.product.id, supplyitem_db.quantity
                )
                supplyitem_db.delete()
                continue

            alter_product_stock(
                Product,
                instance.product.id,
                instance.quantity,
                instance.id,
                SupplyItem,
                negative=True,
            )
            instance.save()
            messages.success(
                self.request,
                f"{instance.product.name}: Dostawa została zaktualizowana.",
            )
        return super().form_valid(form)


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyListView(TemplateView):
    template_name = "supply/supply_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_weekday()
        supply_list = Supply.objects.filter(date_created__gte=previous_friday)
        context["supply_list"] = supply_list
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyDeleteView(SuccessMessageMixin, DeleteView):
    model = Supply
    template_name = "supply/supply_delete.html"
    form_class = DeleteSupplyForm
    success_message = "Dostawa została usunięte."
    success_url = reverse_lazy("supply-list")

    def __init__(self):
        self.producer = None

    def get_object(self, queryset=None):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        supply = (
            Supply.objects.filter(producer=self.producer)
            .order_by("-date_created")
            .first()
        )
        return supply

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["slug"] = self.kwargs["slug"]
        context["producer"] = self.producer.short
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        for item in self.object.supplyitems.all():
            reduce_product_stock(Product, item.product.id, item.quantity)
        self.object.delete()
        return HttpResponseRedirect(success_url)



@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyFromOrdersCreateView(SupplyCreateView):
    success_message = "Dostawa została utworzona."
    template_name = "supply/supply_create_from_orders.html"

    def form_valid(self, form):
        if validate_supply_exists(Supply, form.instance.producer):
            messages.warning(
                self.request,
                f"{form.instance.producer}: Ten producent ma już dostawę na ten tydzień.",
            )
            return self.form_invalid(form)
        form.instance.user = self.request.user
        self.object = form.save()

        supply = Supply.objects.get(id=self.object.id)
        producer = Producer.objects.get(id=form.instance.producer.id)
        products = filter_products_with_ordered_quantity(
            Product).filter(ordered_quantity__gt=0).filter(producer=form.instance.producer.id)
        for product in products:
            if not product.is_stocked:
                SupplyItem.objects.create(supply=supply, product=product, quantity=product.ordered_quantity)
        return HttpResponseRedirect(reverse_lazy("supply-update-form", kwargs={"slug": producer.slug}))
