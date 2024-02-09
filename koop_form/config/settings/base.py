from os import path
from environ import Env

# creates Env class instance with default DEBUG=False if there is no DEBUG var
env = Env(DEBUG=(bool, False))

# creates a base directory, path.dirname returns parent directory of a given file/path
BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

env.read_env(path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesStandaloneBackend",
    # Django ModelBackend is the default authentication backend.
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = path.join(BASE_DIR, "staticfiles")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"

LOGGING_FORMAT_VERBOSE = "%(levelname) %(asctime)s %(threadName) %(thread)d %(module) %(filename) %(lineno)d %(name) %(funcName) %(process)d %(message)"

LOGGING_FORMAT_SIMPLE = (
    "%(levelname) %(asctime)s %(module) %(filename) %(lineno)d %(funcName) %(message)"
)

FORMATTERS = {
    "json-verbose": {
        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "format": LOGGING_FORMAT_VERBOSE,
    },
    "json-simple": {
        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "format": LOGGING_FORMAT_SIMPLE,
    },
    "readable": {
        "format": "%(asctime)s [%(levelname)s/%(name)s:%(lineno)d] " + "%(message)s",
        "datefmt": "%d/%b/%Y %H:%M:%S",
    },
}

HANDLERS = {
    "console_handler": {
        "class": "logging.StreamHandler",
        "formatter": "json-simple",
        "level": "DEBUG",
    },
    "info_handler": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": f"{BASE_DIR}/logs/wks_info.log",
        "mode": "a",
        "encoding": "utf-8",
        "formatter": "readable",
        "level": "INFO",
        "backupCount": 5,
        "maxBytes": 1024 * 1024 * 5,  # 5 MB
    },
    "error_handler": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": f"{BASE_DIR}/logs/wks_error.log",
        "mode": "a",
        "formatter": "readable",
        "level": "WARNING",
        "backupCount": 5,
        "maxBytes": 1024 * 1024 * 5,  # 5 MB
    },
}

LOGGERS = {
    "django": {
        "handlers": ["console_handler", "info_handler"],
        "level": "INFO",
    },
    "django.request": {
        "handlers": ["error_handler"],
        "level": "INFO",
        "propagate": True,
    },
    "django.template": {
        "handlers": ["error_handler"],
        "level": "DEBUG",
        "propagate": True,
    },
    "django.server": {
        "handlers": ["error_handler"],
        "level": "INFO",
        "propagate": True,
    },
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # może być potrzeba zmienić na True, gdy w produkcji logger nie będzie działał
    "formatters": FORMATTERS,
    "handlers": HANDLERS,
    "loggers": LOGGERS,
}

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_TIMEOUT = 30

AXES_FAILURE_LIMIT = 10

AXES_COOLOFF_TIME = 1

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

# na ten moment walidacje idą jako INFO i są nierozróżnialne od prawidłowych requestów hmmmm
