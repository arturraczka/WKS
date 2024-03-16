from django.apps import AppConfig
from django.core.management import call_command




class FormConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.form"

    def ready(self):
        from . import signals
        print(">>>>>>>>>>>>> Form app start")
       # self._test_migrate()



    def _test_migrate(self):
        call_command("migrate")


