import logging
import csv

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q, Prefetch
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import (
    TemplateView,
)

from apps.form.models import Producer, Order, OrderItem, Product
from apps.form.services import (
    calculate_previous_weekday,
    calculate_order_cost,
    calculate_total_income,
    create_order_data_list,
    staff_check,
    get_producers_list,
    filter_products_with_ordered_quantity_and_income,
)

from apps.form.views import ProducersView

logger = logging.getLogger("django.server")


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerProductsReportView(TemplateView):
    template_name = "report/producer_products_report.html"

    def __init__(self, **kwargs):
        super().__init__()
        self.producer = None
        self.products = None
        self.product_names_list = []
        self.product_ordered_quantities_list = []
        self.product_incomes_list = []

    def get_producer_products(self):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])
        self.products = filter_products_with_ordered_quantity_and_income(
            Product, self.producer.id
        )

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
        context[
            "product_ordered_quantities_list"
        ] = self.product_ordered_quantities_list
        context["product_incomes_list"] = self.product_incomes_list
        context["total_income"] = calculate_total_income(self.products)
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerBoxReportView(TemplateView):
    template_name = "report/producer_box_report.html"

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


@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersReportView(TemplateView):
    template_name = "report/users_report.html"

    def __init__(self):
        super().__init__()
        self.previous_friday = calculate_previous_weekday()
        self.user_phone_number_list = []
        self.user_pickup_day_list = []
        self.user_order_number_list = []
        self.user_name_list = []

    def get_users_queryset(self):
        newest_orders = Order.objects.filter(date_created__gte=self.previous_friday)
        prefetch = Prefetch("orders", queryset=newest_orders, to_attr="order")

        users_qs = (
            get_user_model()
            .objects.filter(Q(orders__date_created__gte=self.previous_friday))
            .select_related("userprofile")
            .prefetch_related(prefetch)
        )
        return users_qs

    def get_additional_context(self):
        for user in self.get_users_queryset():
            self.user_name_list.append(user.first_name + " " + user.last_name)
            self.user_order_number_list.append(user.order[0].order_number)
            self.user_pickup_day_list.append(user.order[0].pick_up_day)
            self.user_phone_number_list.append(user.userprofile.phone_number)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()
        context["user_name_list"] = self.user_name_list
        context["user_order_number_list"] = self.user_order_number_list
        context["user_pickup_day_list"] = self.user_pickup_day_list
        context["user_phone_number_list"] = self.user_phone_number_list
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerProductsListView(ProducersView):
    template_name = "report/producer_products_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerBoxListView(ProducerProductsListView):
    template_name = "report/producer_box_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducersFinanceReportView(TemplateView):
    template_name = "report/producers_finance.html"

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
    template_name = "report/order_box_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        orders = Order.objects.filter(
            date_created__gte=calculate_previous_weekday()
        ).order_by("date_created")

        context["orders"] = orders

        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class OrderBoxReportView(OrderBoxListView):
    template_name = "report/order_box_report.html"

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
        product_ids = []

        for item in orderitems:
            product_ids += (item.product.id,)
            orderitems_names += (item.product.name,)
            orderitems_quantity += (str(item.quantity).rstrip("0").rstrip("."),)

        products = Product.objects.filter(id__in=product_ids).select_related("producer")
        for prod in products:
            producer_short += (prod.producer.short,)

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
    template_name = "report/users_finance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        users = get_user_model().objects.all().select_related("userprofile")

        koop_id_list = []
        name_list = []
        order_cost_list = []

        # TODO przyda się logika, że jeśli user nic nie zamówił, to nie pojawi się w raporcie
        for user in users:
            koop_id_list.append(user.userprofile.koop_id)
            name_list += (f"{user.first_name} {user.last_name}",)
            try:
                orderitems = (
                    Order.objects.filter(date_created__gte=calculate_previous_weekday())
                    .get(user=user)
                    .orderitems.select_related("product")
                )
            except ObjectDoesNotExist:
                order_cost = 0
            else:
                order_cost = calculate_order_cost(orderitems) * user.userprofile.fund
            order_cost_list.append(order_cost)

        context["koop_id_list"] = koop_id_list
        context["name_list"] = name_list
        context["order_cost_list"] = order_cost_list

        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class MassProducerBoxReportDownloadView(TemplateView):
    template_name = "report/producer_box_report.html"
    response_class = HttpResponse
    content_type = "text/csv"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_weekday()
        products_qs = (
            Product.objects.prefetch_related("orderitems", "orders")
            .select_related("producer")
            .filter(Q(orders__date_created__gte=previous_friday))
            .annotate(ordered_quantity=Sum("orderitems__quantity"))
            .distinct()
            .order_by("producer__short")
        )
        products_names = []
        products_quantities = []
        products_producers = []
        products_quant_in_stock = []
        for product in products_qs:
            products_names.append(product.name)
            products_quantities.append(product.ordered_quantity)
            if product.quantity_in_stock:
                products_quant_in_stock.append(product.quantity_in_stock + product.ordered_quantity)
            else:
                products_quant_in_stock.append(' ')
            products_producers.append(product.producer.short)
        context["products_producers"] = products_producers
        context["products_quantities"] = products_quantities
        context["products_names"] = products_names
        context["products_quant_in_stock"] = products_quant_in_stock
        context["order_data"] = create_order_data_list(products_qs)
        return context

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": f'attachment; filename="raport-paczkowanie.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(["Producent", "Ilość łącznie", "W magazynie", "Produkt", "Lista skrzynek"])

        for producer, quant, stock, product, boxlist in zip(
            context["products_producers"],
            context["products_quantities"],
            context["products_quant_in_stock"],
            context["products_names"],
            context["order_data"],
        ):
            writer.writerow([producer, quant, stock, product, boxlist])
        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class UsersFinanceReportDownloadView(UsersFinanceReportView):
    pass
