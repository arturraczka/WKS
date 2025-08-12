from .base import *
import sentry_sdk

DEBUG = False
ALLOWED_HOSTS = get_allowed_hosts(ALLOWED_HOSTS_CONFIG_PATH,["koop-formularz.pl", "www.koop-formularz.pl", "64.226.70.181"])
CSRF_TRUSTED_ORIGINS = [ f"https://*.{host}" for host in ALLOWED_HOSTS ]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django_crontab',
    "crispy_forms",
    "crispy_bootstrap5",
    "corsheaders",
    "apps.form",
    "apps.user",
    "apps.report",
    "apps.supply",
    "apps.templates",
    "apps.static",
    "apps.core",
    "django_extensions",
    "import_export",
    "axes",
    "widget_tweaks",
]

CRONTAB_COMMAND_PREFIX=f"ENV_CONFIG_PATH={ENV_CONFIG_PATH}"

CRONJOBS = [
    ('0 0 * * FRI', 'django.core.management.call_command', ['set_product_order_deadline']),
    ('5 20 * * MON', 'django.core.management.call_command', ['send_order_summary_to_users']),
    # Add more cron jobs as needed
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",  # should be the last middleware
]

sentry_sdk.init(
    dsn="https://417ffc5c900466f9e4f901e43501e5ba@o4506717508730880.ingest.sentry.io/4506717510303744",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
    send_default_pii=True,
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

DEFAULT_FROM_EMAIL = "'Koopowy automat' <koophost@gmail.com>"
