from django.urls import path

from apps.supply.views import (
    SupplyCreateView,
    SupplyProductsFormView,
    SupplyUpdateFormView,
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
]
