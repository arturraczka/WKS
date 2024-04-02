from django.urls import path

from apps.report.views import (
    ProducerProductsSuppliesReportView,
    ProducerBoxReportView,
    UsersReportView,
    ProducerBoxListView,
    ProducersFinanceReportView,
    ProducerBoxReportDownloadView,
    UsersReportDownloadView,
    ProducersFinanceReportDownloadView,
    ProducerProductsSuppliesReportDownloadView,
    OrderBoxListView,
    OrderBoxReportView,
    OrderBoxReportDownloadView,
    UsersFinanceReportView,
    ProducerProductsSuppliesListView,
    MassProducerBoxReportDownloadView,
    UsersFinanceReportDownloadView,
    MassOrderBoxReportDownloadView, ProducerProductsReportView, ProducerProductsReportDownloadView,
    ProducerProductsListView, ProductsExcessReportView,
)


urlpatterns = [
    path(
        "producenci-produkty-dostawy/",
        ProducerProductsSuppliesListView.as_view(),
        name="producer-products-supplies-list",
    ),
    path(
        "producenci-produkty/",
        ProducerProductsListView.as_view(),
        name="producer-products-list",
    ),
    path(
        "producenci-produkty-dostawy/<str:slug>/",
        ProducerProductsSuppliesReportView.as_view(),
        name="producer-products-supplies-report",
    ),
    path(
        "producenci-produkty/<str:slug>/",
        ProducerProductsReportView.as_view(),
        name="producer-products-report",
    ),
    path(
        "producenci-skrzynki/",
        ProducerBoxListView.as_view(),
        name="producer-box-list",
    ),
    path(
        "producenci-skrzynki/<str:slug>/",
        ProducerBoxReportView.as_view(),
        name="producer-box-report",
    ),
    path(
        "kooperanci/",
        UsersReportView.as_view(),
        name="users-report",
    ),
    path(
        "producenci-finanse/",
        ProducersFinanceReportView.as_view(),
        name="producers-finance",
    ),
    path(
        "pobierz/producenci-skrzynki/<str:slug>/",
        ProducerBoxReportDownloadView.as_view(),
        name="producer-box-report-download",
    ),
    path(
        "pobierz/kooperanci/",
        UsersReportDownloadView.as_view(),
        name="users-report-download",
    ),
    path(
        "pobierz/producenci-finanse/",
        ProducersFinanceReportDownloadView.as_view(),
        name="producers-finance-report-download",
    ),
    path(
        "pobierz/producenci-produkty-dostawy/<str:slug>/",
        ProducerProductsSuppliesReportDownloadView.as_view(),
        name="producer-products-supplies-report-download",
    ),
    path(
        "pobierz/producenci-produkty/<str:slug>/",
        ProducerProductsReportDownloadView.as_view(),
        name="producer-products-report-download",
    ),
    path(
        "zamowienia-skrzynki/",
        OrderBoxListView.as_view(),
        name="order-box-list",
    ),
    path(
        "zamowienia-skrzynki/<int:pk>/",
        OrderBoxReportView.as_view(),
        name="order-box-report",
    ),
    path(
        "pobierz/zamowienia-skrzynki/<int:pk>/",
        OrderBoxReportDownloadView.as_view(),
        name="order-box-report-download",
    ),
    path(
        "kooperanci-finanse/",
        UsersFinanceReportView.as_view(),
        name="users-finance-report",
    ),
    path(
        "pobierz/wszyscy-producenci-skrzynki/",
        MassProducerBoxReportDownloadView.as_view(),
        name="mass-producer-box-report-download",
    ),
    path(
        "pobierz/kooperanci-finanse/",
        UsersFinanceReportDownloadView.as_view(),
        name="users-finance-report-download",
    ),
    path(
        "pobierz/wszystkie-zamowienia-skrzynki/",
        MassOrderBoxReportDownloadView.as_view(),
        name="mass-order-box-report-download",
    ),
    path(
        "nadwyzki/",
        ProductsExcessReportView.as_view(),
        name="excess-report",
    ),
]
