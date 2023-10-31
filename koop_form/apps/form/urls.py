"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from apps.form.views import (
    ProductsView,
    OrderCreateView,
    OrderProductsView,
    ProducersView,
    OrderUpdateView,
    OrderDeleteView,
    OrderProducersView,
    OrderUpdateFormView,
    ProducerReportView,
)


urlpatterns = [
    path("producenci/", ProducersView.as_view(), name="producer-list"),
    path(
        "producenci/<str:slug>/",
        ProductsView.as_view(),
        name="producer-with-products",
    ),
    path(
        "raporty/producenci/<str:slug>/",
        ProducerReportView.as_view(),
        name="producer-report",
    ),
    path(
        "zamowienie/producenci/",
        OrderProducersView.as_view(),
        name="form-producer-list",
    ),
    path(
        "zamowienie/producenci/<str:slug>/",
        OrderProductsView.as_view(),
        name="orderitem-create",
    ),
    path("zamowienie/nowe/", OrderCreateView.as_view(), name="order-create"),
    path(
        "zamowienie/edytuj-zamowienie/",
        OrderUpdateFormView.as_view(),
        name="order-formset-update",
    ),  # git
    path(
        "zamowienie/szczegoly/<int:pk>/edytuj/",
        OrderUpdateView.as_view(),
        name="order-update",
    ),
    path(
        "zamowienie/szczegoly/<int:pk>/usun/",
        OrderDeleteView.as_view(),
        name="order-delete",
    ),
    # path('zamowienie/szczegoly/', OrderDetailOrderItemListView.as_view(), name='order-detail'),
    # path('zamowienie/szczegoly/produkt/<int:pk>/edytuj/', OrderItemUpdateView.as_view(), name='orderitem-update'),
    # path('zamowienie/szczegoly/produkt/<int:pk>/usun/', OrderItemDeleteView.as_view(), name='orderitem-delete'),
]
