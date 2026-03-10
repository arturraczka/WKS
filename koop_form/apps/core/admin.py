from typing import Any

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from apps.core.models import AppConfig
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db import connection
import csv

from apps.form.models import OrderItem, Product

User = get_user_model()


@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    fields = ["reports_start_day", "homepage_info"]
    change_form_template = "admin/custom_change_form.html"

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        return redirect(
            "admin:core_appconfig_change",
            object_id=AppConfig.load().id,
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "report/",
                self.admin_site.admin_view(self.report_view),
                name="core-report",
            ),
        ]
        return custom + urls

    def report_view(self, request):
        order_count = request.GET.get("order_count") or 10
        report_name = request.GET.get("report_name") or "Raport"
        match report_name:
            case "most_ordered":
                report_name = "Najczęściej zamawiane"
                qs = (
                    Product.objects.select_related("producer")
                    .prefetch_related("orders")
                    .annotate(times_ordered=Count("orders"))
                    .filter(times_ordered__gte=order_count)
                    .order_by("-times_ordered")
                    .values("name", "producer__name", "times_ordered")
                )
            case "least_ordered":
                report_name = "Najrzadziej zamawiane"
                qs = (
                    Product.objects.select_related("producer")
                    .prefetch_related("orders")
                    .annotate(times_ordered=Count("orders"))
                    .filter(times_ordered__lte=order_count)
                    .order_by("-times_ordered")
                    .values("name", "producer__name", "times_ordered")
                )
            case _:
                qs = Product.objects.none()
        columns = list(qs[0].keys()) if qs else []
        rows = [list(row.values()) for row in qs]

        if request.GET.get("format") == "csv":
            return self.export_csv(columns, rows)

        context = dict(
            self.admin_site.each_context(request),
            columns=columns,
            rows=rows,
            report_name=report_name,
        )

        return TemplateResponse(request, "admin/report.html", context)

    def export_csv(self, columns, rows):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="report.csv"'

        writer = csv.writer(response)
        writer.writerow(columns)
        writer.writerows(rows)

        return response
