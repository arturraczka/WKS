import logging

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from apps.core.models import AppConfig

logger = logging.getLogger("django.server")


@method_decorator(login_required, name="dispatch")
class HomepageTemplateView(TemplateView):
    template_name = "core/homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_config"] = AppConfig.load()
        return context
