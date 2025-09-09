from apps.core.models import AppConfig


def app_config(request):
    config = AppConfig.load()
    return {
        "report_interval_start": config.report_interval_start,
        "report_interval_end": config.report_interval_end,
    }
