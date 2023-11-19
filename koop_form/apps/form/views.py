import logging
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum, Q, Prefetch
from django.shortcuts import get_object_or_404
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
    FormView,
    TemplateView,
)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from apps.form.forms import (
    CreateOrderForm,
    CreateOrderItemForm,
    CreateOrderItemFormSet,
    UpdateOrderItemForm,
    UpdateOrderItemFormSet,
)
from apps.form.models import Producer, Order, OrderItem, Product
from django.urls import reverse, reverse_lazy
from apps.form.services import (
    calculate_previous_friday,
    calculate_order_cost,
    calculate_available_quantity,
    calculate_total_income,
    create_order_data_list,
    order_check,
    staff_check,
)
from apps.form.validations import (
    perform_create_orderitem_validations,
    validate_order_exists,
    perform_update_orderitem_validations,
)
from django.forms import modelformset_factory
from django.db.models import F
from django.contrib.auth.mixins import LoginRequiredMixin


logger = logging.getLogger("django.server")


class ProducersView(LoginRequiredMixin, ListView):
    model = Producer
    context_object_name = "producers"
    template_name = "form/producer_list.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Producer.objects.filter(is_active=True)
        return queryset


class ProductsView(LoginRequiredMixin, DetailView):
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
        context["producers"] = Producer.objects.filter(is_active=True)
        return context

    def get_object(self, queryset=None):
        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        return producer


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerListReportView(ProducersView):
    template_name = "form/producer_list_report.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerReportView(LoginRequiredMixin, TemplateView):
    template_name = "form/producer_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_friday()

        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        products = (
            Product.objects.prefetch_related("orderitems")
            .filter(producer=producer)
            .filter(Q(orderitems__item_ordered_date__gte=previous_friday))
            .only("name", "orderitems__quantity")
        )

        products_with_ordered_quantity_and_income = products.annotate(
            ordered_quantity=Sum("orderitems__quantity"),
            income=F("ordered_quantity") * F("price"),
        )
        context["products"] = products_with_ordered_quantity_and_income
        total_income = calculate_total_income(context["products"])
        context["total_income"] = total_income
        return context


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(order_check, login_url='/zamowienie/nowe/'), name="dispatch")
class OrderProducersView(ProducersView):
    template_name = "form/order_producers.html"


@method_decorator(user_passes_test(order_check, login_url='/zamowienie/nowe/'), name="dispatch")
class OrderProductsFormView(LoginRequiredMixin, FormView):
    model = OrderItem
    template_name = "form/order_products_form.html"
    form_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.previous_friday = calculate_previous_friday()
        self.order = None
        self.producer = None
        self.products_with_related = None
        self.products = None
        self.initial_data = None
        self.orderitems = None
        self.order_cost = None
        self.producers = None
        self.products_with_available_quantity = None

    def get_producer_order_and_products(self):
        self.order = Order.objects.get(
            user=self.request.user, date_created__gte=self.previous_friday
        )
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        self.products_with_related = (
            Product.objects.filter(producer=self.producer)
            .filter(is_active=True)
            .prefetch_related("weight_schemes", "statuses")
        )
        self.products = (
            Product.objects.filter(producer=self.producer)
            .filter(is_active=True)
            .only("id")
        )
        self.initial_data = [{"product": product.id} for product in self.products]

    def get_form_class(self):
        self.get_producer_order_and_products()
        order_item_formset = modelformset_factory(
            OrderItem,
            form=CreateOrderItemForm,
            formset=CreateOrderItemFormSet,
            extra=len(self.initial_data),
        )
        return order_item_formset

    def get_success_url(self):
        return self.request.path

    def get_additional_context(self):
        self.orderitems = (
            OrderItem.objects.filter(order=self.order.id)
            .select_related("product")
            .only("product_id", "quantity", "product__price", "product__name")
        )
        self.order_cost = calculate_order_cost(self.orderitems)
        self.producers = Producer.objects.filter(is_active=True).values(
            "slug", "name", "order"
        )  # pytanie: czy używanie values() ma tutaj sens? - ma sens i nawet fajnie byłoby zrobić z tego listę
        self.products_with_available_quantity = calculate_available_quantity(
            self.products_with_related
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()

        products_weight_schemes = []
        for product in self.products_with_related:
            weight_schemes_set = product.weight_schemes.all()
            weight_schemes_quantity_list = [(Decimal(weight_scheme.quantity), f"{weight_scheme.quantity}".rstrip('0').rstrip('.')) for weight_scheme in weight_schemes_set]
            products_weight_schemes.append(weight_schemes_quantity_list)

        for form, scheme in zip(context["form"], products_weight_schemes):
            form.fields['quantity'].choices = scheme

        context["order"] = self.order
        context["orderitems"] = self.orderitems
        context["order_cost"] = self.order_cost
        context["producers"] = self.producers
        context["producer"] = self.producer
        context["products"] = self.products_with_available_quantity
        return context

    def get_initial(self):
        return self.initial_data

    def form_valid(self, form):
        formset = form.save(commit=False)
        for instance in formset:
            if instance.quantity == 0:
                pass
            else:
                if not perform_create_orderitem_validations(instance, self.request):
                    return self.form_invalid(form)
                instance.order = self.order
                instance.save()
                messages.success(
                    self.request,
                    f"{instance.product}: Produkt został dodany do zamówienia.",
                )
        return super().form_valid(form)


class OrderCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
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


@method_decorator(user_passes_test(order_check, login_url='/zamowienie/nowe/'), name="dispatch")
class OrderUpdateFormView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    model = OrderItem
    success_message = "Zamówienie zostało zaktualizowane."
    form_class = None
    template_name = "form/order_update_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.previous_friday = calculate_previous_friday()
        self.order = None
        self.producer = None
        self.products_with_related = None
        self.products = None
        self.orderitems = None

    def get_success_url(self):
        return self.request.path

    def get_producer_order_and_products(self):
        self.order = Order.objects.get(
            user=self.request.user, date_created__gte=self.previous_friday
        )
        self.products_with_related = Product.objects.filter(
            orders=self.order
        ).prefetch_related("weight_schemes", "statuses")
        self.orderitems = OrderItem.objects.filter(order=self.order.id)

    def get_form_class(self):
        self.get_producer_order_and_products()
        order_item_formset = modelformset_factory(
            OrderItem,
            form=UpdateOrderItemForm,
            formset=UpdateOrderItemFormSet,
            edit_only=True,
        )
        return order_item_formset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["queryset"] = self.orderitems
        return kwargs

    # TODO to raczej do refactoringu tak jak w OrderProductFormView
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        orderitems = (
            OrderItem.objects.filter(order=self.order.id)
            .select_related("product")
            .only("product_id", "quantity", "product__price", "product__name")
        )
        context["order"] = self.order
        context["orderitems"] = orderitems

        user_fund = self.request.user.userprofile.fund
        if user_fund is None:
            user_fund = 1.3
        context["fund"] = user_fund
        context["order_cost"] = calculate_order_cost(orderitems)
        context["order_cost_with_fund"] = context["order_cost"] * user_fund

        orderitems_with_forms = zip(
            self.products_with_related, context["orderitems"], context["form"]
        )
        context["orderitems_with_forms"] = orderitems_with_forms
        return context

    def form_valid(self, form):
        formset = form.save(commit=False)
        for instance in formset:
            if not perform_update_orderitem_validations(instance, self.request):
                return self.form_invalid(form)
            instance.order = self.order
            instance.save()
        return super().form_valid(form)


class OrderUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Order
    fields = ["pick_up_day"]
    template_name = "form/order_create.html"
    success_url = reverse_lazy("order-update-form")
    success_message = "Dzień odbioru zamówienia został zmieniony."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


class OrderDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Order
    template_name = "form/order_delete.html"
    success_url = reverse_lazy("producers")
    success_message = "Zamówienie zostało usunięte."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProductsReportView(LoginRequiredMixin, ListView):
    model = Product
    context_object_name = "products"
    template_name = "form/products_report.html"

    def get_queryset(self):
        previous_friday = calculate_previous_friday()
        products_qs = Product.objects.filter(
            Q(orders__date_created__gte=previous_friday)
        ).distinct()
        return products_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = context["products"]
        order_data_list = create_order_data_list(products, Order, OrderItem)
        context["order_data"] = order_data_list
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersReportView(LoginRequiredMixin, TemplateView):
    template_name = "form/users_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_friday()

        newest_order = Order.objects.filter(date_created__gte=previous_friday)
        prefetch = Prefetch('orders', queryset=newest_order, to_attr='order')

        users_qs = get_user_model().objects.filter(
            Q(orders__date_created__gte=previous_friday)
        ).select_related("userprofile").prefetch_related(prefetch)

        context["users"] = users_qs
        return context
