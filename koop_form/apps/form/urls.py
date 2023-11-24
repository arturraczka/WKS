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
    OrderProductsFormView,
    ProducersView,
    OrderUpdateView,
    OrderDeleteView,
    OrderProducersView,
    OrderUpdateFormView,
    ProducerProductsReportView,
    ProducerBoxReportView,
    UsersReportView,
    ProducerProductsListView, ProducerBoxListView,
)


urlpatterns = [
    path("producenci/", ProducersView.as_view(), name="producers"),
    path(
        "producenci/<str:slug>/",
        ProductsView.as_view(),
        name="products",
    ),
    path(
        "raporty/producenci-produkty/",
        ProducerProductsListView.as_view(),
        name="producer-products-list",
    ),
    path(
        "raporty/producenci-produkty/<str:slug>/",
        ProducerProductsReportView.as_view(),
        name="producer-products-report",
    ),
    path(
        "zamowienie/producenci/",
        OrderProducersView.as_view(),
        name="order-producers",
    ),
    path(
        "zamowienie/producenci/<str:slug>/",
        OrderProductsFormView.as_view(),
        name="order-products-form",
    ),
    path("zamowienie/nowe/", OrderCreateView.as_view(), name="order-create"),
    path(
        "zamowienie/edytuj/",
        OrderUpdateFormView.as_view(),
        name="order-update-form",
    ),
    path(
        "zamowienie/szczegoly/edytuj/<int:pk>/",
        OrderUpdateView.as_view(),
        name="order-update",
    ),
    path(
        "zamowienie/szczegoly/usun/<int:pk>/",
        OrderDeleteView.as_view(),
        name="order-delete",
    ),
    path(
        "raporty/producenci-skrzynki/",
        ProducerBoxListView.as_view(),
        name="producer-box-list",
    ),
    path(
        "raporty/producenci-skrzynki/<str:slug>/",
        ProducerBoxReportView.as_view(),
        name="producer-box-report",
    ),
    path(
        "raporty/kooperanci/",
        UsersReportView.as_view(),
        name="users-report",
    ),
]
