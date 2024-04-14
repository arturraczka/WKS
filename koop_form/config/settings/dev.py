from .base import *

DEBUG = True
ALLOWED_HOSTS = get_allowed_hosts(ALLOWED_HOSTS_CONFIG_PATH,["localhost", "127.0.0.1", "mylocal"])
CSRF_TRUSTED_ORIGINS = [ f"https://*.{host}" for host in ALLOWED_HOSTS ]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "debug_toolbar",
    "crispy_forms",
    "crispy_bootstrap5",
    "corsheaders",
    "apps.form",
    "apps.user",
    "apps.report",
    "apps.supply",
    "apps.templates",
    "apps.static",
    "apps.prometheus_proxy",
    "django_extensions",
    "import_export",
    "axes",
    "widget_tweaks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",  # should be the last middleware
]

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
