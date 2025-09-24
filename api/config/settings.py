import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS: list[str] = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # allauth requirements
    "django.contrib.sites",
    # third-party
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # social providers
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "core",
    "apps.accounts",
    "apps.accounts.user",
    "apps.accounts.auth",
    "apps.accounts.founder",
    "apps.company",
    "apps.competitor",
    "apps.funding",
    "apps.revenue",
    "apps.stakeholder",
    "apps.notifications",

]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "api.config.wsgi.application"
ASGI_APPLICATION = "api.config.asgi.application"


if os.getenv("DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = os.getenv("DJANGO_LANGUAGE_CODE", "en-us")
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True


# Static and media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}


# CORS
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL", "true").lower() in {"1", "true", "yes", "on"}
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]


# DRF
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": os.getenv("API_TITLE", "Noev API"),
    "DESCRIPTION": os.getenv("API_DESCRIPTION", "Starter API project"),
    "VERSION": os.getenv("API_VERSION", "0.1.0"),
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api",
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True},
    "POSTPROCESSING_HOOKS": ["api.core.schema_hooks.get_schema_hooks"],
    "PREPROCESSING_FILTERS": ["api.core.schema_hooks.get_preprocessing_filters"],
    "ENUM_NAME_OVERRIDES": {},
    # Enhanced settings to handle ManyToManyField issues
    "DISABLE_ERRORS_AND_WARNINGS": True,
    "ENABLE_DJANGO_DEPLOY_CHECK": False,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "GENERIC_ADDITIONAL_PROPERTIES": False,
    "COMPONENT_SPLIT_PATCH": True,
    "COMPONENT_SPLIT_CREATE": True,
    "SORT_OPERATIONS": False,
    "SORT_TAGS": False,
    "GENERATOR_CLASS": "api.core.schema_generator.CustomSchemaGenerator",
}


# Security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "false").lower() in {"1", "true", "yes", "on"}


# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(name)s %(message)s"},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sites framework
SITE_ID = int(os.getenv("SITE_ID", "1"))

# Custom user model
AUTH_USER_MODEL = "user.User"

# Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "optional")
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# dj-rest-auth
REST_AUTH = {
    "USE_JWT": False,
}

# Email backend (console by default)
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "false").lower() in {"1", "true", "yes", "on"}
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.com")

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in {"1", "true", "yes", "on"}

# Rate Limiter
RATE_LIMITER_ENABLED = os.getenv("RATE_LIMITER_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
RATE_LIMITER_DEFAULT_RATE = int(os.getenv("RATE_LIMITER_DEFAULT_RATE", "5"))
RATE_LIMITER_DEFAULT_PERIOD = int(os.getenv("RATE_LIMITER_DEFAULT_PERIOD", "1"))

# Apply patches for DRF Spectacular issues
try:
    from api.core.model_meta_patch import apply_model_meta_patch
    apply_model_meta_patch()
except ImportError:
    pass
