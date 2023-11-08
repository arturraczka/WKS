from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
    FormView,
)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.form.custom_mixins import OrderExistsTestMixin
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
    order_exists_test,
    filter_objects_prefetch_related,
    calculate_available_quantity,
    calculate_total_income, create_order_data_list,
)
from apps.form.validations import (
    perform_create_orderitem_validations,
    validate_order_exists,
    perform_update_orderitem_validations,
)
from django.forms import modelformset_factory
from django.db.models import F


@method_decorator(login_required, name="dispatch")
class ProducersView(ListView):
    model = Producer
    context_object_name = "producers"
    template_name = "form/producer_list.html"
    paginate_by = 25


@method_decorator(login_required, name="dispatch")
class ProductsView(DetailView):
    model = Producer
    context_object_name = "producer"
    template_name = "form/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["producers"] = Producer.objects.all()
        products_with_related = filter_objects_prefetch_related(
            Product, *["weight_schemes", "statuses"], producer=context["producer"]
        )
        context["products_with_related"] = products_with_related
        return context

    def get_object(self, queryset=None):
        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        return producer


@method_decorator(login_required, name="dispatch")
class ProducerReportView(ListView):
    model = Product
    context_object_name = "products"
    template_name = "form/producer_report.html"

    def get_queryset(self):
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

        return products_with_ordered_quantity_and_income

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_income = calculate_total_income(context["products"])
        context["total_income"] = total_income
        return context


@method_decorator(login_required, name="dispatch")
class OrderProducersView(OrderExistsTestMixin, ProducersView):
    template_name = "form/order_producers.html"

    def test_func(self):
        return order_exists_test(self.request, Order)


@method_decorator(login_required, name="dispatch")
class OrderProductsFormView(OrderExistsTestMixin, SuccessMessageMixin, FormView):
    model = OrderItem
    template_name = "form/order_products_form.html"
    form_class = None
    success_message = "Produkt został dodany do zamówienia."

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
        self.products_with_related = filter_objects_prefetch_related(
            Product, *["weight_schemes", "statuses"], producer=self.producer
        )
        self.products = Product.objects.filter(producer=self.producer).only("id")
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

    def test_func(self):
        return order_exists_test(self.request, Order)

    def get_success_url(self):
        return self.request.path

    def get_additional_context(self):
        self.orderitems = (
            OrderItem.objects.filter(order=self.order.id)
            .select_related("product")
            .only("product_id", "quantity", "product__price", "product__name")
        )
        self.order_cost = calculate_order_cost(self.orderitems)
        self.producers = Producer.objects.all().values(
            "slug", "name", "order"
        )  # pytanie: czy używanie values() ma tutaj sens?
        self.products_with_available_quantity = calculate_available_quantity(
            self.products_with_related
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()

        context["order"] = self.order
        context["orderitems"] = self.orderitems
        context["order_cost"] = self.order_cost
        context["producers"] = self.producers
        context["producer"] = self.producer
        products_with_forms = zip(
            context["form"], self.products_with_available_quantity
        )
        context["products_with_forms"] = products_with_forms
        return context

    def get_initial(self):
        return self.initial_data

    def form_valid(self, form):
        formset = form.save(commit=False)
        for instance in formset:
            if not perform_create_orderitem_validations(instance, self.request):
                return self.form_invalid(form)
            instance.order = self.order
            instance.save()
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class OrderCreateView(SuccessMessageMixin, CreateView):
    model = Order
    template_name = "form/order_create.html"
    form_class = CreateOrderForm
    success_message = "Zamówienie zostało utworzone. Dodaj produkty."

    def form_valid(self, form):
        if validate_order_exists(self.request, Order):
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        producer = Producer.objects.all().order_by("order").first()
        success_url = reverse("order-products-form", kwargs={"slug": producer.slug})
        return success_url


@method_decorator(login_required, name="dispatch")
class OrderUpdateFormView(OrderExistsTestMixin, SuccessMessageMixin, FormView):
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
        self.initial_data = None
        self.orderitems = None

    def test_func(self):
        return order_exists_test(self.request, Order)

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
        self.initial_data = [orderitem for orderitem in self.orderitems.values()]

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
        context["order_cost"] = calculate_order_cost(orderitems)

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


@method_decorator(login_required, name="dispatch")
class OrderUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Order
    fields = ["pick_up_day"]
    template_name = "form/order_create.html"
    success_url = reverse_lazy('order-update-form')
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
class ProductsReportView(ListView):
    model = Product
    context_object_name = "products"
    template_name = "form/products_report.html"

    def get_queryset(self):
        previous_friday = calculate_previous_friday()
        products_qs = Product.objects.filter(Q(orders__date_created__gte=previous_friday)).distinct()
        return products_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = context["products"]
        order_data_list = create_order_data_list(products, Order, OrderItem)
        context["order_data"] = order_data_list
        return context
