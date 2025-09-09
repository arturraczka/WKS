from django.urls import path

from apps.supply.views import (
    SupplyCreateView,
    SupplyProductsFormView,
    SupplyUpdateFormView,
    SupplyListView,
    SupplyDeleteView,
    SupplyFromOrdersCreateView,
)


urlpatterns = [
    path(
        "nowa/",
        SupplyCreateView.as_view(),
        name="supply-create",
    ),
    path(
        "produkty/<str:slug>/",
        SupplyProductsFormView.as_view(),
        name="supply-products-form",
    ),
    path(
        "edytuj/<str:slug>/",
        SupplyUpdateFormView.as_view(),
        name="supply-update-form",
    ),
    path(
        "lista/",
        SupplyListView.as_view(),
        name="supply-list",
    ),
    path(
        "usun/<str:slug>/",
        SupplyDeleteView.as_view(),
        name="supply-delete",
    ),
    path(
        "nowa-z-zamowienia/",
        SupplyFromOrdersCreateView.as_view(),
        name="supply-create-from-orders",
    ),
]
