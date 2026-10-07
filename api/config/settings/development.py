"""
Django development settings.

Enterprise-grade development configuration with:
- Zero duplication - all settings come from centralized config
- Development-optimized defaults
- Environment-aware configuration loading
- Integrated debugging and development tools
"""

import os
from .config_loader import (
    get_environment_config,
    get_api_config,
    get_frontend_config,
    get_config_value,
    get_env_bool,
    get_env_list,
)


from .components.paths import BASE_DIR, GEOIP_PATH
from .components.apps import *
from .components.auth import *
from .components.cache import *
from .components.celery import *
from .components.database import DATABASES as DEFAULT_DATABASES, DEFAULT_AUTO_FIELD
from .components.email import *
from .components.i18n import *
from .components.middleware import *
from .components.rest_framework import *
from .components.security import *
from .components.static import *
from .components.templates import *
from .components.urls import *
from .components.app_specific import *
from .components.onefold import *
from .components.services import *
from .components.ckeditor import *
from .components.third_party import *
from .components.silk import *
from .components.jazzmin import *
from .components.video_ai import *
from .components.card_creation import *
from .components.twilio import *


environment_config = get_environment_config()
api_config = get_api_config()
frontend_config = get_frontend_config()

DATABASES = DEFAULT_DATABASES

DATABASES = DEFAULT_DATABASES


from .components.debug_config import DEBUG


ALLOWED_HOSTS = get_env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1", "*"])

CORS_ALLOW_ALL_ORIGINS = get_env_bool("CORS_ALLOW_ALL_ORIGINS", True)
CORS_ALLOWED_ORIGINS = get_env_list("CORS_ALLOWED_ORIGINS")

CSRF_TRUSTED_ORIGINS = get_env_list("CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = get_env_bool("SSL_REDIRECT", False)
SECURE_COOKIE_SECURE = get_env_bool("COOKIE_SECURE", False)
SECURE_HSTS_SECONDS = int(os.environ.get("HSTS_SECONDS", "0"))


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


def _get_internal_ips():
    """
    Get list of internal IPs for development tools.

    Includes Docker gateway IPs for containerized development.
    """
    internal_ips = [
        "127.0.0.1",
        "localhost",
        "172.19.0.1",
        "host.docker.internal",
    ]

    import socket

    try:
        docker_gateway = socket.gethostbyname("gateway.docker.internal")
        internal_ips.append(docker_gateway)
    except (socket.gaierror, OSError):
        internal_ips.extend(
            [
                "172.17.0.1",
                "172.18.0.1",
                "192.168.65.1",
            ]
        )

    return internal_ips


INTERNAL_IPS = _get_internal_ips()


LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG").upper()


from .components.logging import LOGGING


INSTALLED_APPS = INSTALLED_APPS + DEV_APPS


MIDDLEWARE = MIDDLEWARE + DEV_MIDDLEWARE
