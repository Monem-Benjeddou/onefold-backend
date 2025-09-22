"""
Installed applications for the Django project.
"""

import os


DJANGO_APPS = [
    "jazzmin",
    "daphne",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]


THIRD_PARTY_APPS = [
    "cachalot",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework.authtoken",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "djoser",
    "rosetta",
    "parler",
    "django_celery_results",
    "phonenumber_field",
    "django_countries",
    "taggit",
    "oauth2_provider",
    "social_django",
    "drf_social_oauth2",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "health_check.contrib.redis",
    "anymail",
    "import_export",
    "django_celery_beat",
    "django_q",
    "ckeditor",
    "ckeditor_uploader",
    "mptt",
    "django_filters",
    "channels",
    "channels_redis",
    "storages",
]


LOCAL_APPS = [
    "apps.accounts.user",
    "apps.accounts.auth",
    "apps.accounts.founder",
    "apps.company",
    "apps.competitor",
    "apps.countries",
    "apps.files",
    "apps.funding",
    "apps.internationalization",
    "apps.notifications",
    "apps.privacy",
    "apps.revenue",
    "apps.stakeholder",
    "core",
]


INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


SILK_MIDDLEWARE = [
    "silk.middleware.SilkyMiddleware",
]


PRODUCTION_MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
]


ROOT_URLCONF = "api.config.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                ),
                "templates",
            )
        ],
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


ASGI_APPLICATION = "config.asgi.application"


SITE_ID = 1


DEV_APPS = [
    "silk",
    "django_extensions",
]

DEV_MIDDLEWARE = SILK_MIDDLEWARE


TEST_APPS = []

TEST_MIDDLEWARE = []


PROD_APPS = []

PROD_MIDDLEWARE = PRODUCTION_MIDDLEWARE
