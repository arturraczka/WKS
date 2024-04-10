import logging
import csv
import pandas as pd
from decimal import Decimal

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
    create_order_data_list,
    staff_check,
    get_producers_list,
    filter_products_with_ordered_quantity_income_and_supply_income, filter_products_with_ordered_quantity,
    filter_products_with_supplies_quantity,
)

from apps.form.views import ProducersView
from apps.user.models import UserProfile

logger = logging.getLogger("django.server")


class ProducerTemplateReportView(TemplateView):
    def __init__(self, **kwargs):
        super().__init__()
        self.producer = None
        self.products = None
        self.product_names_list = []

    def get_producer(self):
        self.producer = get_object_or_404(Producer, slug=self.kwargs["slug"])

    def get_products(self):
        pass

    def extract_products_data(self):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_producer()
        self.get_products()
        self.extract_products_data()
        context["producer"] = self.producer
        context["producers"] = get_producers_list(Producer)
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerOrdersReportView(ProducerTemplateReportView):
    template_name = "report/producer_orders_report.html"

    def __init__(self, **kwargs):
        super().__init__()
        self.order_quantities_list = []
        self.order_incomes_list = []
        self.total_order_income = 0

    def get_products(self):
        self.products = filter_products_with_ordered_quantity(
            Product
        ).exclude(Q(income=0)).filter(producer=self.producer.id)

    def extract_products_data(self):
        for product in self.products:
            self.total_order_income += product.income
            self.product_names_list += (product.name,)
            self.order_quantities_list.append(product.ordered_quantity)
            self.order_incomes_list += (f"{Decimal(product.income):.2f}",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product_names_list"] = self.product_names_list
        context["order_quantities_list"] = self.order_quantities_list
        context["order_incomes_list"] = self.order_incomes_list
        context["total_order_income"] = self.total_order_income
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerSuppliesReportView(ProducerTemplateReportView):
    template_name = "report/producer_supplies_report.html"

    def __init__(self, **kwargs):
        super().__init__()
        self.supply_quantities_list = []
        self.supply_incomes_list = []
        self.total_supply_income = 0

    def get_products(self):
        self.products = filter_products_with_supplies_quantity(
            Product
        ).exclude(Q(supply_income=0)).filter(producer=self.producer.id)

    def extract_products_data(self):
        for product in self.products:
            self.total_supply_income += product.supply_income
            self.product_names_list += (product.name,)
            self.supply_quantities_list += (product.supply_quantity,)
            self.supply_incomes_list += (f"{Decimal(product.supply_income):.2f}",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product_names_list"] = self.product_names_list
        context["supply_quantities_list"] = self.supply_quantities_list
        context["supply_incomes_list"] = self.supply_incomes_list
        context["total_supply_income"] = self.total_supply_income
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
            .order_by("last_name")
        )
        return users_qs

    def get_additional_context(self):
        for user in self.get_users_queryset():
            self.user_name_list.append(user.last_name + " " + user.first_name)
            self.user_order_number_list.append(user.order[0].order_number)
            self.user_pickup_day_list.append(user.order[0].pick_up_day)
            try:
                self.user_phone_number_list.append(user.userprofile.phone_number)
            except UserProfile.DoesNotExist:
                self.user_phone_number_list.append("brak telefonu")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_additional_context()
        context["user_name_list"] = self.user_name_list
        context["user_order_number_list"] = self.user_order_number_list
        context["user_pickup_day_list"] = self.user_pickup_day_list
        context["user_phone_number_list"] = self.user_phone_number_list
        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerSuppliesListView(ProducersView):
    template_name = "report/producer_supplies_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerOrdersListView(ProducersView):
    template_name = "report/producer_orders_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerBoxListView(ProducerSuppliesListView):
    template_name = "report/producer_box_list.html"


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducersFinanceReportView(TemplateView):
    template_name = "report/producers_finance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producers = Producer.objects.filter(is_active=True).order_by("name")

        producers_names = []
        producers_incomes = []
        producers_supply_incomes = []

        total_incomes = 0
        total_supply_incomes = 0

        for producer in producers:
            products_with_orders = filter_products_with_ordered_quantity(Product).filter(producer=producer)
            products_with_supplies = filter_products_with_supplies_quantity(Product).filter(producer=producer)

            aggregated_order_income = products_with_orders.aggregate(total_income=Sum("income"))
            aggregated_supply_income = products_with_supplies.aggregate(total_supply_income=Sum("supply_income"))

            total_order_income = aggregated_order_income["total_income"]
            total_supply_income = aggregated_supply_income["total_supply_income"]
            if total_order_income == 0 and total_supply_income == 0:
                continue
            producers_names += (producer.short,)
            if total_order_income:
                total_incomes += total_order_income
                producers_incomes += (f"{total_order_income:.2f}",)
            else:
                producers_incomes.append(Decimal("0"))

            if total_supply_income:
                total_supply_incomes += total_supply_income
                producers_supply_incomes += (f"{total_supply_income:.2f}",)
            else:
                producers_supply_incomes.append(Decimal("0"))

        context["producers_incomes"] = producers_incomes
        context["producers_supply_incomes"] = producers_supply_incomes
        context["producers_names"] = producers_names

        context["total_incomes"] = total_incomes
        context["total_supply_incomes"] = total_supply_incomes

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
        writer.writerow(["Nazwa producenta", "Kwoty zamówień", "Kwoty dostaw"])
        for name, total_income, total_supply_income in zip(
            context["producers_names"],
            context["producers_incomes"],
            context["producers_supply_incomes"],
        ):
            writer.writerow(
                [
                    name,
                    str(total_income).replace(".", ","),
                    str(total_supply_income).replace(".", ","),
                ]
            )

        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerSuppliesReportDownloadView(ProducerSuppliesReportView):
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": f'attachment; filename="raport-producent-dostawy:-{context["producer"].short}.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                context["producer"].name,
            ]
        )
        writer.writerow(
            [
                "Kwota dostawy (zł):",
                f'{context["total_supply_income"]:.2f}'.replace(".", ","),
            ]
        )
        writer.writerow(
            [
                "Nazwa produktu",
                "Dostarczona ilość",
                "Kwota z dostawy",
            ]
        )
        for name, supply_quantity, supply_income in zip(
            context["product_names_list"],
            context["supply_quantities_list"],
            context["supply_incomes_list"],
        ):
            writer.writerow(
                [
                    name,
                    str(supply_quantity).replace(".", ","),
                    str(supply_income).replace(".", ","),
                ]
            )
        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class OrderBoxListView(TemplateView):
    template_name = "report/order_box_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous_friday = calculate_previous_weekday()
        orders = Order.objects.filter(date_created__gte=previous_friday).order_by(
            "date_created"
        )

        context["orders"] = orders

        return context


@method_decorator(user_passes_test(staff_check), name="dispatch")
class OrderBoxReportView(OrderBoxListView):
    template_name = "report/order_box_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order = get_object_or_404(Order, id=self.kwargs["pk"])
        context["order"] = order
        try:
            context["fund"] = order.user.userprofile.fund
        except UserProfile.DoesNotExist:
            context["fund"] = Decimal("1.3")
        context["username"] = order.user.first_name + " " + order.user.last_name

        orderitems = (
            OrderItem.objects.filter(order=order)
            .select_related("product")
            .order_by("product__producer__short", "product__name")
        )

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
            orderitems_quantity.append(str(item.quantity).rstrip("0").rstrip(".").replace(".", ","))

        products = (
            Product.objects.filter(id__in=product_ids)
            .select_related("producer")
            .order_by("producer__short", "name")
        )
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
            "Content-Disposition": f'attachment; filename="raport-zamowienie-skrzynka:{context["order"].order_number}.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                f'{context["username"]}; skrzynka {context["order"].order_number}; do zapłaty: {context["order_cost_with_fund"]} zł; fundusz {context["fund"]}',
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
    template_name = "report/users_finance_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        users = (
            get_user_model()
            .objects.all()
            .select_related("userprofile")
            .order_by("orders__order_number")
            .filter(orders__date_created__gte=calculate_previous_weekday())
        )

        name_list = []
        order_cost_list = []
        email_list = []
        order_number_list = []
        user_fund_list = []
        order_cost_fund_list = []

        for user in users:
            try:
                order = (
                    Order.objects.filter(date_created__gte=calculate_previous_weekday())
                    .get(user=user)
                )
            except ObjectDoesNotExist:
                continue
            except Order.MultipleObjectsReturned:
                continue
            else:
                orderitems = order.orderitems.select_related("product")
                try:
                    user_fund = user.userprofile.fund
                except UserProfile.DoesNotExist:
                    user_fund = Decimal("1.3")
                order_cost = calculate_order_cost(orderitems)
                order_cost_fund = order_cost * user_fund

            user_fund_list.append(user_fund)
            order_cost_list.append(order_cost)
            order_cost_fund_list.append(str(format(order_cost_fund, ".1f")).replace(".", ","))

            email_list.append(user.email)
            name_list += (f"{user.last_name} {user.first_name}",)
            order_number_list.append(order.order_number)

        context["name_list"] = name_list
        context["email_list"] = email_list
        context["order_number_list"] = order_number_list
        context["order_cost_list"] = order_cost_list
        context["user_fund_list"] = user_fund_list
        context["order_cost_fund_list"] = order_cost_fund_list
        context["zipped"] = zip(name_list, email_list, order_number_list, order_cost_list, user_fund_list, order_cost_fund_list)

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
            products_names.append(str(product.name)[0:-5])
            products_quantities.append(str(product.ordered_quantity).rstrip("0").rstrip(".").replace(".", ","))
            if product.quantity_in_stock:
                products_quant_in_stock.append(str(product.quantity_in_stock + product.ordered_quantity).rstrip("0").rstrip(".").replace(".", ","))
            else:
                products_quant_in_stock.append(" ")
            products_producers.append(product.producer.short)
        context["products_producers"] = products_producers
        context["products_quantities"] = products_quantities
        context["products_names"] = products_names
        context["products_quant_in_stock"] = products_quant_in_stock
        context["order_data"] = create_order_data_list(products_qs)
        return context

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": 'attachment; filename="raport-paczkowanie.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            ["Producent", "Ilość łącznie", "W magazynie", "Produkt", "Lista skrzynek"]
        )

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
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": 'attachment; filename="raport-finanse-kooperantów.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(["imie nazwisko", "koop ID", "kwota zamowienia", "fundusz", "kwota z funduszem", "numer skrzynki"])
        for name, email, order_cost, fund, order_fund, number in zip(
            context["name_list"],
            context["email_list"],
            context["order_cost_list"],
            context["user_fund_list"],
            context["order_cost_fund_list"],
            context["order_number_list"],
        ):
            writer.writerow([
                name,
                email,
                str(order_cost).replace(".", ","),
                str(fund).replace(".", ","),
                str(order_fund).replace(".", ","),
                number,
            ])

        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class MassOrderBoxReportDownloadView(TemplateView):
    template_name = "report/order_box_report.html"
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": 'attachment; filename="raport-zamowienia-skrzynki-wszystkie.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )

        # writer = csv.writer(response)

        previous_friday = calculate_previous_weekday()
        orders_queryset = Order.objects.filter(
            date_created__gt=previous_friday
        ).order_by("order_number")

        data = {}
        df = pd.DataFrame(data)

        for order in orders_queryset:
            try:
                fund = order.user.userprofile.fund
            except UserProfile.DoesNotExist:
                fund = Decimal("1.3")
            username = order.user.first_name + " " + order.user.last_name

            orderitems = OrderItem.objects.filter(order=order).select_related("product")

            order_cost = calculate_order_cost(orderitems)
            order_cost_with_fund = f"{order_cost * fund:.2f}"

            producer_short = []
            orderitems_names = []
            orderitems_quantity = []
            product_ids = []

            for item in orderitems:
                product_ids += (item.product.id,)
                orderitems_names += (item.product.name,)
                orderitems_quantity += (str(item.quantity).rstrip("0").rstrip(".").replace(".", ","),)

            products = Product.objects.filter(id__in=product_ids).select_related(
                "producer"
            )
            for prod in products:
                producer_short += (prod.producer.short,)

            first_row = pd.DataFrame({
                f"skrzynka {order.order_number}": ["Producent"],
                f"{username} do zapłaty {order_cost_with_fund} zł": ["Nazwa produktu"],
                f"fundusz {fund}": ["Zamówiona ilość"],
                "-": [" ",],
            }, index=[0])

            new_df = pd.DataFrame({
                f"skrzynka {order.order_number}": producer_short,
                f"{username} do zapłaty {order_cost_with_fund} zł": orderitems_names,
                f"fundusz {fund}": orderitems_quantity,
                "-": [" "] * len(producer_short),
            })

            joined_df = pd.concat([first_row, new_df], ignore_index=True)
            df = pd.concat([df, joined_df], axis=1)

        df.to_csv(response, index=False)
        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProducerOrdersReportDownloadView(ProducerOrdersReportView):
    response_class = HttpResponse
    content_type = "text/csv"

    def render_to_response(self, context, **response_kwargs):
        headers = {
            "Content-Disposition": f'attachment; filename="raport-producent-zamowienia:-{context["producer"].short}.csv"'
        }

        response = self.response_class(
            content_type=self.content_type,
            headers=headers,
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                context["producer"].name,
            ]
        )
        writer.writerow(
            [
                "Kwota zamówienia (zł):",
                f'{context["total_order_income"]:.2f}'.replace(".", ","),
            ]
        )
        writer.writerow(
            [
                "Nazwa produktu",
                "Zamówiona ilość",
                "Kwota z zamówienia",
            ]
        )
        for name, quantity, income in zip(
            context["product_names_list"],
            context["order_quantities_list"],
            context["order_incomes_list"],
        ):
            if not quantity:
                continue
            writer.writerow(
                [
                    name,
                    str(quantity).replace(".", ","),
                    str(income).replace(".", ","),
                ]
            )
        return response


@method_decorator(user_passes_test(staff_check), name="dispatch")
class ProductsExcessReportView(TemplateView):
    template_name = "report/products_excess_report.html"

    def __init__(self, **kwargs):
        super().__init__()
        self.products = None

    def get_products(self):
        self.products = filter_products_with_ordered_quantity_income_and_supply_income(
            Product, producer_id=None, filter_producer=False
        ).filter(excess__gt=0).filter(is_stocked=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.get_products()
        context["products"] = self.products
        return context
