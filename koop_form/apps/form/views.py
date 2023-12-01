import copy
import logging
import csv

from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum, Q, Prefetch
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy
from django.forms import modelformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
    FormView,
    TemplateView,
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
    calculate_previous_weekday,
    calculate_order_cost,
    calculate_available_quantity,
    calculate_total_income,
    create_order_data_list,
    order_check,
    staff_check,
    get_producers_list,
    add_choices_to_forms,
    filter_products_with_ordered_quantity_and_income,
    add_choices_to_form,
    get_users_last_order,
    get_orderitems_query, check_if_form_is_open,

)
from apps.form.validations import (
    perform_create_orderitem_validations,
    validate_order_exists,
    perform_update_orderitem_validations,
)

logger = logging.getLogger("django.server")


@method_decorator(login_required, name="dispatch")
class ProducersView(ListView):
    model = Producer
    context_object_name = "producers"
    template_name = "form/producer_list.html"
    paginate_by = 25

    def get_queryset(self):
        return get_producers_list(Producer)


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
        context["producers"] = get_producers_list(Producer)
        return context

    def get_object(self, queryset=None):
        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        return producer


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerProductsListView(ProducersView):
    template_name = "form/producer_products_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerProductsReportView(LoginRequiredMixin, TemplateView):
    template_name = "form/producer_products_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        context["producer"] = producer
        context["producers"] = get_producers_list(Producer)
        products = filter_products_with_ordered_quantity_and_income(Product, producer)
        context["products"] = products
        total_income = calculate_total_income(context["products"])
        context["total_income"] = total_income
        return context


@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderProducersView(ProducersView):
    template_name = "form/order_producers.html"


@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderProductsFormView(LoginRequiredMixin, FormOpenMixin, FormView):
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
        return self.request.path

    def get_producer_object(self):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])

    def get_products_query(self):
        self.products = (
            Product.objects.filter(producer=self.producer)
            .filter(is_active=True)
            .only("id")
        )

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
            .prefetch_related("weight_schemes", "statuses")
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

        add_choices_to_forms(context["form"], self.products_with_quantity)
        context["order"] = self.order
        context["orderitems"] = self.orderitems
        context["order_cost"] = calculate_order_cost(self.orderitems)

        context["producers"] = get_producers_list(Producer)
        context["producer"] = self.producer
        context["products"] = self.products_with_quantity
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


@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderUpdateFormView(LoginRequiredMixin, FormOpenMixin, FormView):
    model = OrderItem
    form_class = None
    template_name = "form/order_update_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = None
        self.producer = None
        self.products_with_related = None
        self.products = None
        self.orderitems = None

    def get_success_url(self):
        return self.request.path

    def get_producer_order_and_products(self):
        self.order = get_users_last_order(Order, self.request.user)
        self.products_with_related = Product.objects.filter(
            orders=self.order
        ).prefetch_related("weight_schemes", "statuses")
        self.orderitems = get_orderitems_query(OrderItem, self.order.id)

    def get_form_class(self):
        self.get_producer_order_and_products()
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
        context["orderitems"] = self.orderitems
        context["order_cost"] = calculate_order_cost(self.orderitems)
        context["order_cost_with_fund"] = context["order_cost"] * context["fund"]

        products_with_quantity = calculate_available_quantity(self.products_with_related)
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


class OrderUpdateView(
    LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView
):
    model = Order
    fields = ["pick_up_day"]
    template_name = "form/order_create.html"
    success_url = reverse_lazy("order-update-form")
    success_message = "Dzień odbioru zamówienia został zmieniony."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


class OrderDeleteView(
    LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView
):
    model = Order
    template_name = "form/order_delete.html"
    success_url = reverse_lazy("producers")
    success_message = "Zamówienie zostało usunięte."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerBoxReportView(LoginRequiredMixin, TemplateView):
    template_name = "form/producer_box_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_weekday()

        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        context["producer"] = producer

        products_qs = (
            Product.objects.prefetch_related("orderitems")
            .filter(Q(orders__date_created__gte=previous_friday))
            .filter(producer=producer)
            .annotate(ordered_quantity=Sum("orderitems__quantity"))
            .distinct()
        )

        context["producers"] = get_producers_list(Producer)
        context["products"] = products_qs
        order_data_list = create_order_data_list(context["products"], Order, OrderItem)
        context["order_data"] = order_data_list
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersReportView(LoginRequiredMixin, TemplateView):
    template_name = "form/users_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_weekday()

        newest_order = Order.objects.filter(date_created__gte=previous_friday)
        prefetch = Prefetch("orders", queryset=newest_order, to_attr="order")

        users_qs = (
            get_user_model()
            .objects.filter(Q(orders__date_created__gte=previous_friday))
            .select_related("userprofile")
            .prefetch_related(prefetch)
        )

        context["users"] = users_qs
        return context


class ProducerBoxListView(ProducerProductsListView):
    template_name = "form/producer_box_list.html"


# TODO bardzo nieoptymalne query, 6 powtórzeń
@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducersFinanceReportView(LoginRequiredMixin, TemplateView):
    template_name = "form/producers_finance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producers = Producer.objects.filter(is_active=True)

        producers_income = []
        for producer in producers:
            products = filter_products_with_ordered_quantity_and_income(
                Product, producer
            )
            total_income = calculate_total_income(products)
            producers_income.append([producer.name, total_income])
        logger.info(producers_income)
        context["producers_income"] = producers_income

        return context


@login_required()
@user_passes_test(order_check, login_url="/zamowienie/nowe/")
def product_search_view(request):
    queryset = Product.objects.none()
    form = SearchForm(request.GET)

    if form.is_valid():
        search_query = form.cleaned_data.get("search_query")
        if search_query:
            queryset = Product.objects.filter(name__icontains=search_query)

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


@method_decorator(
    user_passes_test(order_check, login_url="/zamowienie/nowe/"), name="dispatch"
)
class OrderItemFormView(LoginRequiredMixin, FormOpenMixin, FormView):
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
        product = Product.objects.filter(id=self.kwargs["pk"])
        self.product_with_quantity = calculate_available_quantity(product)
        self.orderitems = get_orderitems_query(OrderItem, self.order.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()

        add_choices_to_form(context["form"], self.product_with_quantity)
        context["product"] = get_object_or_404(self.product_with_quantity)
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


class ProducerBoxReportDownloadView(ProducerBoxReportView):
    response_class = HttpResponse
    content_type = "text/csv"


    def render_to_response(self, context, **response_kwargs):
        headers = {"Content-Disposition": f'attachment; filename="raport-skrzynki: {context["producer"].short}.csv"'}

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(["Produkt", "Skrzynki",])
        for product, box in zip(context["products"], context["order_data"]):
            writer.writerow([product, box])

        return response
