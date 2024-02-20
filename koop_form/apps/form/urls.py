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
    OrderItemFormView,
    product_search_view,
    main_page_redirect, OrderProductsAllFormView,
)


urlpatterns = [
    path("", main_page_redirect, name="main-page"),
    path("producenci/", ProducersView.as_view(), name="producers"),
    path(
        "producenci/<str:slug>/",
        ProductsView.as_view(),
        name="products",
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
    path("wyszukiwarka/", product_search_view, name="product-search"),
    path(
        "wyszukiwarka/produkt/<int:pk>",
        OrderItemFormView.as_view(),
        name="order-item-form",
    ),
    path(
        "zamowienie/produkty/",
        OrderProductsAllFormView.as_view(),
        name="order-products-all-form",
    ),
]
