from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from apps.core.models import AppConfig


@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    fields = ["reports_start_day", "homepage_info"]

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
