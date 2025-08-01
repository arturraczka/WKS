import copy
import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
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
from apps.form.models import Producer, Order, OrderItem, Product, Category
from apps.form.forms import (
    CreateOrderForm,
    CreateOrderItemForm,
    CreateOrderItemFormSet,
    UpdateOrderItemForm,
    UpdateOrderItemFormSet,
    SearchForm,
    DeleteOrderForm,
)
from apps.form.services import (
    calculate_order_cost,
    order_check,
    get_producers_list,
    add_choices_to_form,
    get_users_last_order,
    get_orderitems_query,
    add_weight_schemes_as_choices_to_forms,
    get_orderitems_query_with_related_order,
    add_producer_list_to_context,
    reduce_product_stock,
    alter_product_stock,
    calculate_order_number,
)
from apps.form.validations import (
    perform_create_orderitem_validations,
    validate_order_exists,
    perform_update_orderitem_validations,
)
from django.core.paginator import Paginator

from apps.user.models import UserProfile

logger = logging.getLogger("django.server")


@method_decorator(login_required, name="dispatch")
class ProducersView(ListView):
    model = Producer
    context_object_name = "producers"
    template_name = "form/producer_list.html"
    paginate_by = 100

    def get_queryset(self):
        return get_producers_list(Producer)


@method_decorator(login_required, name="dispatch")
class ProductsView(DetailView):
    model = Producer
    context_object_name = "producer"
    template_name = "form/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = (
            Product.objects.filter(producer=context["producer"])
            .filter(is_active=True)
            .prefetch_related(
                "weight_schemes",
                "statuses",
            )
            .select_related("producer")
            .select_related("category")
        )
        add_producer_list_to_context(context, Producer)
        return context

    def get_object(self, queryset=None):
        if self.kwargs["slug"] == "pierwszy":
            producer = Producer.objects.filter(is_active=True).first()
        else:
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
    products_per_page = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = None
        self.producer = None
        self.products = None
        self.paginated_products = None
        self.initial_data = []
        self.available_quantities_list = []
        self.products_weight_schemes = []
        self.product_count = 0

    def get_success_url(self):
        page_number = self.request.GET.get("page")
        return str(self.request.path) + f"?page={page_number}"

    def get_order_and_producer(self):
        self.order = get_users_last_order(Order, self.request.user)
        if self.kwargs["slug"] == "pierwszy":
            self.producer = Producer.objects.filter(is_active=True).first()
        else:
            self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])

    def get_products_queryset(self):
        self.products = (
            Product.objects.filter(producer=self.producer)
            .filter(is_active=True)
            .filter(producer__is_active=True)
            # .filter(~Q(quantity_in_stock=0))
            .order_by("category", "name")
            .prefetch_related(
                "weight_schemes",
                "statuses",
            )
            .select_related("producer")
            .select_related("category")
        )

    def paginate_products(self):
        page_number = self.request.GET.get("page")
        products_paginator = Paginator(self.products, self.products_per_page)
        self.paginated_products = products_paginator.get_page(page_number)

    def extract_data_from_products(self):
        for product in self.paginated_products:
            self.product_count += 1
            self.initial_data.append({"product": product.id, "order": self.order})
            weight_schemes = []
            for scheme in product.weight_schemes.all():
                weight_schemes.append(
                    (
                        Decimal(scheme.quantity),
                        f"{scheme.quantity}".rstrip("0").rstrip("."),
                    )
                )
            self.products_weight_schemes.append(weight_schemes)
            self.available_quantities_list.append(product.quantity_in_stock)

    def get_view_data(self):
        self.get_order_and_producer()
        self.get_products_queryset()
        self.paginate_products()
        self.extract_data_from_products()

    def get_form_class(self):
        self.get_view_data()
        order_item_formset = modelformset_factory(
            OrderItem,
            form=CreateOrderItemForm,
            formset=CreateOrderItemFormSet,
            extra=self.product_count,
        )
        return order_item_formset

    def get_initial(self):
        return self.initial_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        context["orderitems"] = get_orderitems_query(OrderItem, self.order.id)
        context["order_cost"] = calculate_order_cost(context["orderitems"])
        context["producer"] = self.producer
        add_producer_list_to_context(context, Producer)
        context["management_form"] = context["form"].management_form
        context["paginated_products"] = self.paginated_products
        add_weight_schemes_as_choices_to_forms(
            context["form"], self.products_weight_schemes
        )
        context["zipped"] = zip(self.paginated_products, context["form"], self.available_quantities_list)
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
                    pass
                else:
                    instance.save()
                    messages.success(
                        self.request,
                        f"{instance.product.name}: Produkt został dodany do zamówienia.",
                    )
                    reduce_product_stock(
                        Product, instance.product.id, instance.quantity
                    )
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class OrderCreateView(FormOpenMixin, SuccessMessageMixin, CreateView):
    model = Order
    template_name = "form/order_create.html"
    form_class = CreateOrderForm
    success_message = "Zamówienie zostało utworzone. Dodaj produkty."

    def form_valid(self, form):
        if validate_order_exists(self.request):
            return self.form_invalid(form)

        form.instance.user = self.request.user
        form.instance.order_number = calculate_order_number(Order)
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse("order-products-all-form")
        return success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["update"] = False
        return context


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderUpdateFormView(FormOpenMixin, FormView):
    # TODO 2: DISPLAY USER BALANCE IN ORDER SUMMARY
    # TODO TOTALNIE DO REFAKTOROWANIA
    model = OrderItem
    form_class = None
    template_name = "form/order_update_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = None
        self.producer = None
        self.products_with_related = None
        self.orderitems = None
        self.products_description = []
        self.products_weight_schemes = []
        self.available_quantities_list = []
        self.product_price_list = []
        self.amounts_list = []

    def get_success_url(self):
        return self.request.path

    def get_order_and_orderitems(self):
        self.order = get_users_last_order(Order, self.request.user)
        self.orderitems = get_orderitems_query_with_related_order(
            OrderItem, self.order.id
        )

    def get_form_class(self):
        self.get_order_and_orderitems()
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
        try:
            user_fund = self.request.user.userprofile.fund.value
        except UserProfile.DoesNotExist:
            user_fund = Decimal("1.3")
        if user_fund is None:
            user_fund = Decimal("1.3")
        return user_fund

    def get_products_with_related(self):
        products_ids = Product.objects.filter(orders=self.order).values_list(
            "id", flat=True
        )
        self.products_with_related = (
            Product.objects.filter(pk__in=list(products_ids))
            .prefetch_related(
                "weight_schemes",
                "statuses",
            )
            .select_related("producer")
            .order_by("name")
        )

    def extract_data_from_products(self):
        for product in self.products_with_related:
            self.products_description.append(product.description)
            weight_schemes = []
            for scheme in product.weight_schemes.all():
                weight_schemes.append(
                    (
                        Decimal(scheme.quantity),
                        f"{scheme.quantity}".rstrip("0").rstrip("."),
                    )
                )
            self.products_weight_schemes.append(weight_schemes)
            self.available_quantities_list.append(product.quantity_in_stock)
            self.product_price_list.append(product.price)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_products_with_related()
        self.extract_data_from_products()

        for price, item in zip(self.product_price_list, self.orderitems):
            self.amounts_list.append(price * item.quantity)

        context[
            "user_name"
        ] = f"{self.request.user.first_name} {self.request.user.last_name}"
        context["fund"] = self.get_user_fund()
        context["order"] = self.order
        context["orderitems"] = self.orderitems
        context["order_cost"] = calculate_order_cost(self.orderitems)
        context["order_cost_with_fund"] = context["order_cost"] * context["fund"]
        context["products"] = self.products_with_related
        context["amounts_list"] = self.amounts_list

        context["products_description"] = self.products_description
        context["products_weight_schemes"] = self.products_weight_schemes
        add_weight_schemes_as_choices_to_forms(
            context["form"], self.products_weight_schemes
        )
        context["available_quantities_list"] = self.available_quantities_list

        return context

    def form_valid(self, form):
        formset = form.save(commit=False)

        for instance in formset:
            if instance.quantity == 0:
                orderitem_db = OrderItem.objects.get(id=instance.id)
                reduce_product_stock(
                    Product,
                    orderitem_db.product.id,
                    orderitem_db.quantity,
                    negative=True,
                )
                orderitem_db.delete()
                continue

            if not perform_update_orderitem_validations(instance, self.request):
                continue

            alter_product_stock(
                Product, instance.product.id, instance.quantity, instance.id, OrderItem
            )
            instance.save()
            messages.success(
                self.request,
                f"{instance.product.name}: Zamówienie zostało zaktualizowane.",
            )

        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class OrderUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Order
    template_name = "form/order_create.html"
    form_class = CreateOrderForm
    success_url = reverse_lazy("order-update-form")
    success_message = "Dzień odbioru zamówienia został zmieniony."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"update": True})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["update"] = True
        return context


@method_decorator(login_required, name="dispatch")
class OrderDeleteView(
    FormOpenMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView
):
    model = Order
    form_class = DeleteOrderForm
    template_name = "form/order_delete.html"
    success_url = reverse_lazy("products", kwargs={"slug": "pierwszy"})
    success_message = "Zamówienie zostało usunięte."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user

    def form_valid(self, form):
        success_url = self.get_success_url()
        for item in self.object.orderitems.all():
            reduce_product_stock(Product, item.product.id, item.quantity, negative=True)
        self.object.delete()
        return HttpResponseRedirect(success_url)


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
        self.product = None

    def get_initial(self):
        self.order = get_users_last_order(Order, self.request.user)
        return {"product": self.kwargs["pk"], "order": self.order}

    def get_additional_context(self):
        self.product = Product.objects.filter(id=self.kwargs["pk"]).filter(
            ~Q(quantity_in_stock=0)
        )
        self.orderitems = get_orderitems_query(OrderItem, self.order.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()

        context["products"] = [
            get_object_or_404(self.product),
        ]
        add_choices_to_form(context["form"], self.product.first())
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
                reduce_product_stock(
                    Product, saved_form.product.id, saved_form.quantity
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
            queryset = (
                Product.objects.filter(name__icontains=search_query)
                .filter(~Q(quantity_in_stock=0))
                .filter(is_active=True)
                .filter(producer__is_active=True)
                .order_by("-category", "price")
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


def main_page_redirect(request):
    obj = Producer.objects.filter(is_active=True).first()
    response = redirect(obj)
    return response


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderProductsAllFormView(OrderProductsFormView):
    template_name = "form/order_products_all_form.html"

    def get_products_queryset(self):
        self.products = (
            Product.objects.filter(is_active=True)
            .filter(producer__is_active=True)
            # .filter(~Q(quantity_in_stock=0))
            .order_by("producer__name", "name")
            .prefetch_related(
                "weight_schemes",
                "statuses",
            )
            .select_related("producer", "category")
        )

    def get_order_and_producer(self):
        self.order = get_users_last_order(Order, self.request.user)
        self.producer = Producer.objects.filter(is_active=True).first()


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderCategoriesFormView(OrderProductsFormView):
    model = OrderItem
    template_name = "form/order_categories_form.html"
    form_class = None
    products_per_page = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = None

    def get_order_and_producer(self):
        self.order = get_users_last_order(Order, self.request.user)
        self.producer = Producer.objects.filter(is_active=True).first()
        if self.kwargs["name"] == "pierwsza":
            self.category = Category.objects.all().first()
        else:
            self.category = get_object_or_404(Category, name=self.kwargs["name"])

    def get_products_queryset(self):
        self.products = (
            Product.objects.filter(category=self.category)
            .filter(is_active=True)
            .filter(producer__is_active=True)
            # .filter(~Q(quantity_in_stock=0))
            .order_by("category", "name")
            .prefetch_related(
                "weight_schemes",
                "statuses",
            )
            .select_related("producer")
            .select_related("category")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["categories"] = Category.objects.all()
        return context
