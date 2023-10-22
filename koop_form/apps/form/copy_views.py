from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from apps.form.forms import CreateOrderForm, CreateOrderItemForm
from apps.form.models import Product, Producer, Order, OrderItem
from django.contrib import messages
from django.urls import reverse


@method_decorator(login_required, name="dispatch")
class ProducerProductListView(ListView):
    model = Product
    context_object_name = "product_list"
    paginate_by = 100
    template_name = "form/producer_with_products.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.producer: object

    def get_queryset(self):
        self.producer = get_object_or_404(Producer, name=self.kwargs["producer"])
        return Product.objects.filter(producer=self.producer, is_visible=True).order_by(
            "name"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["producer"] = self.producer
        if not isinstance(self.request.user, AnonymousUser):
            try:
                context["order"] = Order.objects.get(
                    user=self.request.user, is_archived=False
                ).orderitems.all()
            # except ObjectDoesNotExist:
            except Order.DoesNotExist:
                pass
        return context


@method_decorator(login_required, name="dispatch")
class CreateOrderView(SuccessMessageMixin, CreateView):
    model = Order
    template_name = "form/order_create.html"
    form_class = CreateOrderForm
    success_message = "Zamówienie utworzone. Dodaj produkty."

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse(
            "order-detail",
            kwargs={"pk": self.object.pk, "user": self.request.user.username},
        )
        return success_url


@method_decorator(login_required, name="dispatch")
class OrderOrderItemListView(UserPassesTestMixin, ListView):
    model = OrderItem
    context_object_name = "orderitem_list"
    paginate_by = 100
    template_name = "form/order_orderitems.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order: object

    def test_func(self):
        self.order = get_object_or_404(Order, pk=self.kwargs["pk"])
        return self.request.user == self.order.user

    def get_queryset(self):
        return OrderItem.objects.filter(order=self.order).order_by("product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context


@method_decorator(login_required, name="dispatch")
class CreateOrderItemView(SuccessMessageMixin, CreateView):
    model = OrderItem
    template_name = "form/orderitem_create.html"
    form_class = CreateOrderItemForm
    success_url = ""  # is it legit?
    success_message = "Produkt dodany do zamówienia."

    def get_success_url(self):
        success_url = reverse(
            "order-detail",
            kwargs={"pk": self.object.order.pk, "user": self.request.user.username},
        )
        return success_url

    def form_valid(self, form):
        order = get_object_or_404(Order, user=self.request.user, is_archived=False)
        product = form.cleaned_data["product"]

        # product already in order validation
        if order.products.filter(pk=product.id).exists():
            messages.warning(self.request, "Dodałeś już ten produkt do zamówienia.")
            return self.form_invalid(form)
        else:
            form.instance.product = product
            form.instance.order = order

        # weight scheme validation
        if form.instance.quantity not in product.weight_schemes.all().values_list(
            "quantity", flat=True
        ):
            messages.error(
                self.request,
                "Nieprawidłowa waga zamawianego produtku. Wybierz wagę z dostępnego schematu.",
            )
            return self.form_invalid(form)

        # order deadline validation
        if product.order_deadline and product.order_deadline < timezone.now():
            messages.error(
                self.request,
                "Termin minął, nie możesz już dodać tego produktu do zamówienia.",
            )
            return self.form_invalid(form)

        # max order validation
        order_max_quantity = form.instance.product.order_max_quantity
        if order_max_quantity:
            ordered_quantity = product.orderitems.aggregate(
                ordered_quantity=Sum("quantity")
            )["ordered_quantity"]
            if order_max_quantity < ordered_quantity + form.cleaned_data["quantity"]:
                messages.error(
                    self.request,
                    "Przekroczona maksymalna ilość zamawianego produktu. Nie ma tyle.",
                )
                return self.form_invalid(form)

        # # messages.success(self.request, "Produkt dodany do zamówienia.")  # chyba tego nie potrzebuję, bo dodałem SuccessMessageMixin
        return super().form_valid(form)


# być może i tak muszę połączyć te dwa widoki
