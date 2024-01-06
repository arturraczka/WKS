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
from apps.form.models import Producer, Order, OrderItem, Product, Supply, SupplyItem
from apps.form.forms import (
    CreateOrderForm,
    CreateOrderItemForm,
    CreateOrderItemFormSet,
    UpdateOrderItemForm,
    UpdateOrderItemFormSet,
    SearchForm,
    CreateSupplyForm,
    CreateSupplyItemFormSet,
    CreateSupplyItemForm,
    UpdateSupplyItemFormSet,
    UpdateSupplyItemForm,
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
    get_orderitems_query,
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


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerProductsListView(ProducersView):
    template_name = "form/producer_products_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerProductsReportView(TemplateView):
    template_name = "form/producer_products_report.html"

    def __init__(self, **kwargs):
        super().__init__()
        self.producer = None
        self.products = None
        self.product_names_list = []
        self.product_ordered_quantities_list = []
        self.product_incomes_list = []

    def get_producer_products(self):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        self.products = filter_products_with_ordered_quantity_and_income(Product, self.producer.id)

    def get_product_names_quantities_incomes(self):
        for product in self.products:
            self.product_names_list += (product.name,)
            self.product_ordered_quantities_list.append(product.ordered_quantity)
            self.product_incomes_list += (f"{product.income:.2f}",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_producer_products()
        self.get_product_names_quantities_incomes()
        context["producer"] = self.producer
        context["producers"] = get_producers_list(Producer)
        context["product_names_list"] = self.product_names_list
        context["product_ordered_quantities_list"] = self.product_ordered_quantities_list
        context["product_incomes_list"] = self.product_incomes_list
        context["total_income"] = calculate_total_income(self.products)
        return context


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

        context["order"] = self.order
        context["orderitems"] = self.orderitems
        context["order_cost"] = calculate_order_cost(self.orderitems)

        context["producers"] = get_producers_list(Producer)
        context["producer"] = self.producer
        context["products"] = self.products_with_quantity

        page_number = self.request.GET.get("page")
        products_paginator = Paginator(self.products_with_quantity, 50)
        context["products"] = products_paginator.get_page(page_number)
        context["form_for_management"] = context["form"]
        form_paginator = Paginator(context["form"], 50)
        context["form"] = form_paginator.get_page(page_number)
        add_choices_to_forms(context["form"], context["products"])
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
class OrderUpdateView(
    UserPassesTestMixin, SuccessMessageMixin, UpdateView
):
    model = Order
    fields = ["pick_up_day"]
    template_name = "form/order_create.html"
    success_url = reverse_lazy("order-update-form")
    success_message = "Dzień odbioru zamówienia został zmieniony."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


@method_decorator(login_required, name="dispatch")
class OrderDeleteView(
    UserPassesTestMixin, SuccessMessageMixin, DeleteView
):
    model = Order
    template_name = "form/order_delete.html"
    success_url = reverse_lazy("producers")
    success_message = "Zamówienie zostało usunięte."

    def test_func(self):
        order = get_object_or_404(Order, id=self.kwargs["pk"])
        return self.request.user == order.user


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerBoxReportView(TemplateView):
    template_name = "form/producer_box_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_weekday()

        producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        context["producer"] = producer

        products_qs = (
            Product.objects.prefetch_related("orderitems", "orders")
            .filter(Q(orders__date_created__gte=previous_friday))
            .filter(producer=producer)
            .annotate(ordered_quantity=Sum("orderitems__quantity"))
            .distinct()
        )

        context["producers"] = get_producers_list(Producer)
        context["products"] = products_qs
        order_data_list = create_order_data_list(context["products"])
        context["order_data"] = order_data_list
        return context


# TODO refactoring
@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersReportView(TemplateView):
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

        user_name_list = []
        user_order_number_list = []
        user_pickup_day_list = []
        user_phone_number_list = []

        for user in users_qs:
            user_name_list.append(user.first_name + " " + user.last_name)
            user_order_number_list.append(user.order[0].order_number)
            user_pickup_day_list.append(user.order[0].pick_up_day)
            user_phone_number_list.append(user.userprofile.phone_number)

        context["user_name_list"] = user_name_list
        context["user_order_number_list"] = user_order_number_list
        context["user_pickup_day_list"] = user_pickup_day_list
        context["user_phone_number_list"] = user_phone_number_list

        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerBoxListView(ProducerProductsListView):
    template_name = "form/producer_box_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducersFinanceReportView(TemplateView):
    template_name = "form/producers_finance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producers = Producer.objects.filter(is_active=True)

        producers_names = []
        producers_incomes = []
        for producer in producers:
            products = filter_products_with_ordered_quantity_and_income(
                Product, producer
            )
            total_income = calculate_total_income(products)

            producers_names += (producer.short,)
            producers_incomes += (f"{total_income:.2f}",)

        context["producers_incomes"] = producers_incomes
        context["producers_names"] = producers_names

        return context


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


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerBoxReportDownloadView(ProducerBoxReportView):
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": f'attachment; filename="raport-producent-skrzynka: {context["producer"].short}.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "Produkt",
                "Skrzynki",
            ]
        )
        for product, box in zip(context["products"], context["order_data"]):
            writer.writerow([product, box])

        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersReportDownloadView(UsersReportView):
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": 'attachment; filename="raport-koordynacja-kooperantów.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            ["Imię i nazwisko", "Numer skrzynki", "Dzień odbioru", "Numer telefonu"]
        )
        for name, number, day, phone in zip(
            context["user_name_list"],
            context["user_order_number_list"],
            context["user_pickup_day_list"],
            context["user_phone_number_list"],
        ):
            writer.writerow([name, number, day, phone])

        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducersFinanceReportDownloadView(ProducersFinanceReportView):
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": 'attachment; filename="raport-producenci-finanse.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(["Nazwa producenta", "Suma zamówień"])
        for name, total in zip(
            context["producers_names"],
            context["producers_incomes"],
        ):
            writer.writerow([name, total])

        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerProductsReportDownloadView(ProducerProductsReportView):
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": f'attachment; filename="raport-producent-produkty: {context["producer"].short}.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                f'Przychód łącznie: {context["total_income"]:.2f} zł',
                context["producer"].name,
            ]
        )
        writer.writerow(["Nazwa produktu", "Zamówiona ilość", "Przychód"])
        for name, quantity, income in zip(
            context["products_names"],
            context["products_ordered_quantity"],
            context["products_incomes"],
        ):
            writer.writerow([name, quantity, income])

        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class OrderBoxListView(TemplateView):
    template_name = "form/order_box_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        orders = Order.objects.filter(
            date_created__gte=calculate_previous_weekday()
        ).order_by("date_created")

        context["orders"] = orders

        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class OrderBoxReportView(OrderBoxListView):
    template_name = "form/order_box_report.html"

    def get_user_fund(self):
        user_fund = self.request.user.userprofile.fund
        if user_fund is None:
            user_fund = 1.3
        return user_fund

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["fund"] = self.get_user_fund()

        order = get_object_or_404(Order, id=self.kwargs["pk"])
        context["order"] = order

        orderitems = OrderItem.objects.filter(order=order).select_related("product")

        context["order_cost"] = calculate_order_cost(orderitems)
        context[
            "order_cost_with_fund"
        ] = f'{context["order_cost"] * context["fund"]:.2f}'

        producer_short = []
        orderitems_names = []
        orderitems_quantity = []

        for item in orderitems:
            producer_short += (item.product.producer.short,)
            orderitems_names += (item.product.name,)
            orderitems_quantity += (str(item.quantity).rstrip("0").rstrip("."),)

        context["producer_short"] = producer_short
        context["orderitems_names"] = orderitems_names
        context["orderitems_quantity"] = orderitems_quantity

        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class OrderBoxReportDownloadView(OrderBoxReportView):
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": f'attachment; filename="raport-zamowienie-skrzynka: {context["order"].order_number}.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                ".",
                f'Skrzynka {context["order"].order_number}; do zapłaty: {context["order_cost_with_fund"]} zł; fundusz {context["fund"]}',
            ]
        )
        writer.writerow(["Producent", "Nazwa produktu", "Zamówiona ilość"])
        for short, name, quantity in zip(
            context["producer_short"],
            context["orderitems_names"],
            context["orderitems_quantity"],
        ):
            writer.writerow([short, name, quantity])

        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersFinanceReportView(TemplateView):
    template_name = "form/users_finance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        users = get_user_model().objects.all().select_related("userprofile")

        koop_id_list = []
        name_list = []
        order_cost_list = []

        for user in users:
            koop_id_list.append(user.userprofile.koop_id)
            name_list += (f"{user.first_name} {user.last_name}",)
            orderitems = (
                Order.objects.filter(date_created__gte=calculate_previous_weekday())
                .get(user=user)
                .orderitems.select_related("product")
            )

            order_cost = calculate_order_cost(orderitems) * user.userprofile.fund
            order_cost_list.append(order_cost)

        context["koop_id_list"] = koop_id_list
        context["name_list"] = name_list
        context["order_cost_list"] = order_cost_list

        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersFinanceReportDownloadView(UsersFinanceReportView):
    pass


@method_decorator(user_passes_test(staff_check), name="dispatch")
class SupplyCreateView(SuccessMessageMixin, CreateView):
    model = Supply
    template_name = "form/supply_create.html"
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
    template_name = "form/supply_products_form.html"
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
        self.supply = (
            Supply.objects.filter(producer=self.producer)
            .order_by("-date_created")
            .first()
        )
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
    template_name = "form/supply_update_form.html"

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
