from django.urls import path

from apps.form.views import (
    ProductsView,
    OrderCreateView,
    OrderProductsFormView,
    OrderUpdateView,
    OrderDeleteView,
    OrderProducersView,
    OrderUpdateFormView,
    OrderItemFormView,
    product_search_view,
    OrderProductsAllFormView, OrderCategoriesFormView, OrderAdminRedirectView,
)


urlpatterns = [
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
    path(
        "zamowienie/kategorie/<str:name>/",
        OrderCategoriesFormView.as_view(),
        name="order-categories-form",
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
    path(
        "zamowienie/admin/cofnij-rozliczenie/<int:pk>/",
        OrderAdminRedirectView.as_view(),
        name="undo-order-settlement",
    ),
]
