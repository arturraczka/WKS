from django.urls import re_path
from apps.prometheus_proxy.views import prometheus_request_handler

urlpatterns = [
    re_path(r"^api/v1/.*$", prometheus_request_handler.query, name="prometheus-query")
]