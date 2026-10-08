"""
Onefold settings. Everything environment-specific comes from environment
variables (see .env.example); there is one settings module for all environments.
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DEBUG", False)

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set SECRET_KEY (required when DEBUG is off).")
    SECRET_KEY = "dev-only-insecure-key-never-use-this-in-production"

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

# Where the web app lives; magic links point here.
FRONTEND_URL = env("FRONTEND_URL", "http://localhost:3000").rstrip("/")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.learning",
    "apps.projects",
    "apps.verification",
    "apps.workspace",
]

MIDDLEWARE = [
    "apps.core.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ------------------------------------------------------------------
# PostgreSQL when POSTGRES_DB is set (Docker, production); SQLite otherwise, so
# `python manage.py runserver` works with no setup.
if env("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER", "postgres"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "localhost"),
            "PORT": env("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

# --- Cache & Celery --------------------------------------------------------------
REDIS_URL = env("REDIS_URL")
CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}
        if REDIS_URL
        else {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    )
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", REDIS_URL or "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TIME_LIMIT = 120

# --- API -----------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # JWT plus a check that the token's device session hasn't been revoked.
        "apps.accounts.authentication.SessionJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "EXCEPTION_HANDLER": "apps.core.exceptions.exception_handler",
    # Which X-Forwarded-For entry is the real client for rate limits. In
    # production set it to the number of proxies that append to the header
    # (e.g. 1 for a load balancer); unset trusts the whole header (dev only).
    "NUM_PROXIES": int(env("NUM_PROXIES")) if env("NUM_PROXIES") else None,
    "DEFAULT_THROTTLE_RATES": {
        # Per client IP. Failed password attempts have their own lockout (below).
        "auth": env("THROTTLE_AUTH", "30/min"),
        "auth_email": env("THROTTLE_AUTH_EMAIL", "10/hour"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "30"))),
    "ROTATE_REFRESH_TOKENS": True,
    # A used refresh token can't be replayed; logout revokes the current one.
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "TOKEN_REFRESH_SERIALIZER": "apps.accounts.serializers.SessionTokenRefreshSerializer",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Onefold API",
    "DESCRIPTION": "Learn to ship complete products: paths, projects and verification.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", FRONTEND_URL)

# --- Email ---------------------------------------------------------------------
# docker compose sends every email to Mailpit (a local inbox at
# http://localhost:8025). Without it, development prints emails to the console.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Onefold <hello@localhost>")
EMAIL_TIMEOUT = 10
# Shown in development so nobody has to read logs to find an email.
DEV_MAIL_INBOX_URL = env("DEV_MAIL_INBOX_URL", "") if DEBUG else ""

# --- Security --------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# --- I18n & static -------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Onefold -------------------------------------------------------------------
# Content-as-code root; contains a `paths/` directory. See content/README.md.
LEARNING_CONTENT_DIR = Path(env("LEARNING_CONTENT_DIR", BASE_DIR / "content"))
LEARNING_DEFAULT_PATH = env("LEARNING_DEFAULT_PATH", "ship-your-first-product")
# "Check my work" requests allowed per builder per minute.
VERIFICATION_CHECKS_PER_MINUTE = int(env("VERIFICATION_CHECKS_PER_MINUTE", "10"))
# Emailed links: sign-in, password reset, email confirmation.
MAGIC_LINK_TTL_MINUTES = int(env("MAGIC_LINK_TTL_MINUTES", "15"))
MAGIC_LINK_COOLDOWN_SECONDS = int(env("MAGIC_LINK_COOLDOWN_SECONDS", "60"))
PASSWORD_RESET_TTL_MINUTES = int(env("PASSWORD_RESET_TTL_MINUTES", "30"))
VERIFY_EMAIL_TTL_HOURS = int(env("VERIFY_EMAIL_TTL_HOURS", "72"))
# Failed password sign-ins: after this many for one email within the window,
# that email is locked out until the window passes.
LOGIN_MAX_FAILURES = int(env("LOGIN_MAX_FAILURES", "5"))
LOGIN_LOCKOUT_MINUTES = int(env("LOGIN_LOCKOUT_MINUTES", "15"))

# Sign in with GitHub / Google. A provider is offered only when both values are set.
# Callback URL to register with the provider: FRONTEND_URL/api/auth/oauth/<provider>/callback
GITHUB_CLIENT_ID = env("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = env("GITHUB_CLIENT_SECRET", "")
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", "")

# One-click "Sign in as" demo accounts on the login page. Development only:
# it can never be on when DEBUG is off.
DEMO_LOGIN = DEBUG and env_bool("DEMO_LOGIN", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
