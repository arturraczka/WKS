import copy
import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy
from django.forms import modelformset_factory
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
    FormView,
)

from apps.form.custom_mixins import FormOpenMixin
from apps.form.models import Producer, Order, OrderItem, Product
from apps.form.forms import (
    CreateOrderForm,
    CreateOrderItemForm,
    CreateOrderItemFormSet,
    UpdateOrderItemForm,
    UpdateOrderItemFormSet,
    SearchForm,
)
from apps.form.services import (
    calculate_order_cost,
    calculate_available_quantity,
    order_check,
    get_producers_list,
    add_choices_to_forms,
    add_choices_to_form,
    get_users_last_order,
    get_orderitems_query, add_weight_schemes_as_choices_to_forms,
)
from apps.form.validations import (
    perform_create_orderitem_validations,
    validate_order_exists,
    perform_update_orderitem_validations,
)
from django.core.paginator import Paginator

logger = logging.getLogger("django.server")


@method_decorator(login_required, name="dispatch")
class ProducersView(ListView):
    model = Producer
    context_object_name = "producers"
    template_name = "form/producer_list.html"
    paginate_by = 25

    def get_queryset(self):
        return get_producers_list(Producer)


@method_decorator(login_required, name="dispatch")
class ProductsView(DetailView):
    model = Producer
    context_object_name = "producer"
    template_name = "form/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["products_with_related"] = (
            Product.objects.filter(producer=context["producer"])
            .filter(is_active=True)
            .prefetch_related("weight_schemes", "statuses")
        )
        context["producers"] = get_producers_list(Producer)
        return context

    def get_object(self, queryset=None):
        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        return producer


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderProducersView(ProducersView):
    template_name = "form/order_producers.html"


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderProductsFormView(FormOpenMixin, FormView):
    model = OrderItem
    template_name = "form/order_products_form.html"
    form_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = None
        self.producer = None
        self.products = None
        self.products_with_quantity = None
        self.orderitems = None

    def get_success_url(self):
        page_number = self.request.GET.get("page")
        return str(self.request.path) + f"?page={page_number}"

    def get_producer_object(self):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])

    def get_products_query(self):
        products = (
            Product.objects.filter(producer=self.producer)
            .filter(is_active=True)
            .filter(~Q(quantity_in_stock=0))
            .order_by("category", "name")
            .only("id")
        )
        page_number = self.request.GET.get("page")
        form_paginator = Paginator(products, 50)
        self.products = form_paginator.get_page(page_number)

    def get_order_producer_products(self):
        self.order = get_users_last_order(Order, self.request.user)
        self.get_producer_object()
        self.get_products_query()

    def get_form_class(self):
        self.get_order_producer_products()
        order_item_formset = modelformset_factory(
            OrderItem,
            form=CreateOrderItemForm,
            formset=CreateOrderItemFormSet,
            extra=len(self.products),
        )
        return order_item_formset

    def get_initial(self):
        return [
            {"product": product.id, "order": self.order} for product in self.products
        ]

    def get_products_with_available_quantity_query(self):
        products_with_related = (
            Product.objects.filter(producer=self.producer)
            .filter(is_active=True)
            .filter(~Q(quantity_in_stock=0))
            .prefetch_related(
                "weight_schemes",
                "statuses",
            )
        )
        self.products_with_quantity = calculate_available_quantity(
            products_with_related
        )

    def get_additional_context(self):
        self.get_products_with_available_quantity_query()
        self.orderitems = get_orderitems_query(OrderItem, self.order.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()

        available_quantities_list = []
        products_name = []
        products_category = []
        products_price = []
        products_description = []
        products_statuses = []
        products_weight_schemes = []
        for product in self.products_with_quantity:
            products_name.append(product.name)
            products_price.append(product.price)
            products_description.append(product.description)
            statuses = []
            for status in product.statuses.all():
                statuses.append(status.status_type)
            products_statuses.append(statuses)
            weight_schemes = []
            for scheme in product.weight_schemes.all():
                weight_schemes.append(
                    (
                        Decimal(scheme.quantity),
                        f"{scheme.quantity}".rstrip("0").rstrip("."),
                    )
                )
            products_weight_schemes.append(weight_schemes)
            products_category.append(product.category)
            available_quantities_list.append(product.available_quantity)

        context["order"] = self.order  # TODO
        context["orderitems"] = self.orderitems
        context["order_cost"] = calculate_order_cost(self.orderitems)  # TODO

        context["producers"] = get_producers_list(Producer)  # TODO
        context["producer"] = self.producer  # TODO
        context["management_form"] = context["form"].management_form

        prods_per_pg = 50

        page_number = self.request.GET.get("page")
        form_paginator = Paginator(context["form"], prods_per_pg)

        available_quantities_list_paginator = Paginator(available_quantities_list, prods_per_pg)
        products_name_paginator = Paginator(products_name, prods_per_pg)
        products_category_paginator = Paginator(products_category, prods_per_pg)
        products_price_paginator = Paginator(products_price, prods_per_pg)
        products_description_paginator = Paginator(products_description, prods_per_pg)
        products_statuses_paginator = Paginator(products_statuses, prods_per_pg)
        products_weight_schemes_paginator = Paginator(products_weight_schemes, prods_per_pg)

        context["form"] = form_paginator.get_page(page_number)

        context["available_quantities_list"] = available_quantities_list_paginator.get_page(page_number)
        context["products_description"] = products_description_paginator.get_page(page_number)

        context["zipped_products_data"] = zip(
            products_name_paginator.get_page(page_number),
            products_price_paginator.get_page(page_number),
            products_category_paginator.get_page(page_number),
            products_statuses_paginator.get_page(page_number),
        )

        add_weight_schemes_as_choices_to_forms(context["form"], products_weight_schemes_paginator.get_page(page_number))
        return context

    def form_valid(self, form):
        formset = form.save(commit=False)
        for instance in formset:
            if instance.quantity == 0:
                pass
            else:
                if not perform_create_orderitem_validations(
                    instance, self.request, Order, Product
                ):
                    return self.form_invalid(form)
                else:
                    instance.save()
                    messages.success(
                        self.request,
                        f"{instance.product.name}: Produkt został dodany do zamówienia.",
                    )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class OrderCreateView(SuccessMessageMixin, CreateView):
    model = Order
    template_name = "form/order_create.html"
    form_class = CreateOrderForm
    success_message = "Zamówienie zostało utworzone. Dodaj produkty."

    def form_valid(self, form):
        if validate_order_exists(self.request):
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        producer = Producer.objects.all().order_by("order").first()
        success_url = reverse("order-products-form", kwargs={"slug": producer.slug})
        return success_url


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderUpdateFormView(FormOpenMixin, FormView):
    model = OrderItem
    form_class = None
    template_name = "form/order_update_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = None
        self.producer = None
        self.products_with_related = None
        # self.products = None
        self.orderitems = None

    def get_success_url(self):
        return self.request.path

    # TODO czy self.products_with_related musi być tutaj zdefiniowane??
    def get_order_orderitems_and_products(self):
        self.order = get_users_last_order(Order, self.request.user)

        products_ids = (
            Product.objects.filter(orders=self.order)
            .values_list(flat=True)
            .order_by("name")
        )
        self.products_with_related = (
            Product.objects.filter(pk__in=list(products_ids))
            .prefetch_related(
                "weight_schemes",
                "statuses",
            )
            .order_by("name")
        )

        self.orderitems = get_orderitems_query(OrderItem, self.order.id)

    def get_form_class(self):
        self.get_order_orderitems_and_products()
        order_item_formset = modelformset_factory(
            OrderItem,
            form=UpdateOrderItemForm,
            formset=UpdateOrderItemFormSet,
            edit_only=True,
            extra=0,
        )
        return order_item_formset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["queryset"] = self.orderitems
        return kwargs

    def get_user_fund(self):
        user_fund = self.request.user.userprofile.fund
        if user_fund is None:
            user_fund = 1.3
        return user_fund

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fund"] = self.get_user_fund()
        context["order"] = self.order
        self.orderitems = get_orderitems_query(
            OrderItem, self.order.id
        )  # I am calling this query second time
        # (first time is for form initial data), for calculating correct order cost
        # after user has tried to post invalid data
        context["orderitems"] = self.orderitems
        context["order_cost"] = calculate_order_cost(self.orderitems)
        context["order_cost_with_fund"] = context["order_cost"] * context["fund"]

        products_with_quantity = calculate_available_quantity(
            self.products_with_related
        ).order_by("name")
        add_choices_to_forms(context["form"], products_with_quantity)

        context["products"] = products_with_quantity
        return context

    def form_valid(self, form):
        formset = form.save(commit=False)
        for instance in formset:
            if not perform_update_orderitem_validations(instance, self.request):
                return self.form_invalid(form)
            instance.save()
            messages.success(
                self.request,
                f"{instance.product.name}: Zamówienie zostało zaktualizowane.",
            )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class OrderUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Order
    fields = ["pick_up_day"]
    template_name = "form/order_create.html"
    success_url = reverse_lazy("order-update-form")
    success_message = "Dzień odbioru zamówienia został zmieniony."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


@method_decorator(login_required, name="dispatch")
class OrderDeleteView(UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Order
    template_name = "form/order_delete.html"
    success_url = reverse_lazy("producers")
    success_message = "Zamówienie zostało usunięte."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderItemFormView(FormOpenMixin, FormView):
    model = OrderItem
    template_name = "form/order_item_form.html"
    form_class = CreateOrderItemForm
    success_url = "/wyszukiwarka/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = None
        self.orderitems = None
        self.product_with_quantity = None

    def get_initial(self):
        self.order = get_users_last_order(Order, self.request.user)
        return {"product": self.kwargs["pk"], "order": self.order}

    def get_additional_context(self):
        product = Product.objects.filter(id=self.kwargs["pk"]).filter(
            ~Q(quantity_in_stock=0)
        )
        self.product_with_quantity = calculate_available_quantity(product)
        self.orderitems = get_orderitems_query(OrderItem, self.order.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()

        context["product"] = get_object_or_404(self.product_with_quantity)
        add_choices_to_form(context["form"], self.product_with_quantity)
        context["order"] = self.order
        context["orderitems"] = self.orderitems
        context["order_cost"] = calculate_order_cost(self.orderitems)
        return context

    def form_valid(self, form):
        saved_form = copy.deepcopy(form).save(commit=False)
        if saved_form.quantity == 0:
            pass
        else:
            if not perform_create_orderitem_validations(
                saved_form, self.request, Order, Product
            ):
                return self.form_invalid(form)
            else:
                saved_form.save()
                messages.success(
                    self.request,
                    f"{saved_form.product.name}: Produkt został dodany do zamówienia.",
                )
        return super().form_valid(saved_form)


@login_required()
@user_passes_test(order_check, login_url="/zamowienie/nowe/")
def product_search_view(request):
    queryset = Product.objects.none()
    form = SearchForm(request.GET)

    if form.is_valid():
        search_query = form.cleaned_data.get("search_query")
        if search_query:
            queryset = Product.objects.filter(name__icontains=search_query).filter(
                ~Q(quantity_in_stock=0)
            )

    order = get_users_last_order(Order, request.user)
    orderitems = get_orderitems_query(OrderItem, order.id)
    order_cost = calculate_order_cost(orderitems)

    context = {
        "form": form,
        "products": queryset,
        "order_cost": order_cost,
        "order": order,
        "orderitems": orderitems,
    }

    return render(request, "form/product_search.html", context)
