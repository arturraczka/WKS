from django.apps import AppConfig
from django.db.models.signals import post_migrate


class FormConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.form"

    def ready(self):
        from . import signals
        from apps.form.signals import init_weight_scheme_with_zero
        post_migrate.connect(init_weight_scheme_with_zero, sender=self)




