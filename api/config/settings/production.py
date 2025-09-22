"""
Django production settings.

Enterprise-grade production configuration with:
- Zero duplication - all settings come from centralized config
- Security-first approach - all sensitive data from environment variables
- Environment-aware configuration loading
- Robust error handling and fallbacks
"""

import os
from pathlib import Path
from decouple import config
from logging.config import dictConfig
from .config_loader import (
    get_environment_config,
    get_aws_config,
    get_redis_config,
    get_config_value,
    get_env_bool,
    get_env_list,
    get_env_int,
)
from redis.exceptions import ConnectionError, TimeoutError


BASE_DIR = Path(__file__).resolve().parent.parent.parent


from .components.paths import GEOIP_PATH
from .components.apps import *
from .components.auth import *
from .components.cache import *
from .components.celery import *
from .components.database import (
    DATABASES as DEFAULT_DATABASES,
    DEFAULT_AUTO_FIELD,
    DATABASES_PROD,
)
from .components.email import *
from .components.i18n import *
from .components.middleware import *
from .components.rest_framework import *
from .components.security import *
from .components.static import *
from .components.templates import *
from .components.urls import *
from .components.app_specific import *
from .components.services import *
from .components.ckeditor import *
from .components.third_party import *
from .components.jazzmin import *
from .components.video_ai import *
from .components.card_creation import *
from .components.twilio import *
from .components.logging import LOGGING_PROD

environment_config = get_environment_config()
aws_config = get_aws_config()
redis_config = get_redis_config()


from .components.debug_config import DEBUG

TESTING = False


DEFAULT_ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "kolct-api.neothons.com",
]

ALLOWED_HOSTS = get_env_list("ALLOWED_HOSTS", DEFAULT_ALLOWED_HOSTS)

CORS_ALLOW_ALL_ORIGINS = get_env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CORS_ALLOWED_ORIGINS = get_env_list("CORS_ALLOWED_ORIGINS")

CSRF_TRUSTED_ORIGINS = get_env_list("CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = get_env_bool("SSL_REDIRECT", True)
SECURE_COOKIE_SECURE = get_env_bool("COOKIE_SECURE", True)
SECURE_HSTS_SECONDS = get_env_int("HSTS_SECONDS", 31536000)


DATABASES = DATABASES_PROD


USE_S3_ENV = get_env_bool("USE_S3", False)
USE_S3 = USE_S3_ENV and aws_config["ACCESS_KEY_ID"] and aws_config["SECRET_ACCESS_KEY"]

if USE_S3_ENV and not USE_S3:
    print("⚠️  USE_S3=true but missing credentials - falling back to local storage")
elif USE_S3:
    print(f"✅ S3 storage enabled with bucket: {aws_config['STORAGE_BUCKET_NAME']}")


PRE_SECURITY_MIDDLEWARE = [
    "core.middlewares.deployment_health.DeploymentHealthMiddleware",
    "core.middlewares.deployment_health.SSLBypassForHealthMiddleware",
]


PRODUCTION_MIDDLEWARE = [
    "core.middlewares.health_check.HealthCheckSSLBypassMiddleware",
    "core.middlewares.redis_fallback.RedisConnectionMiddleware",
]


if not USE_S3:
    try:
        import whitenoise

        PRODUCTION_MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")
        print("✅ WhiteNoise middleware enabled for static file serving")
    except ImportError:
        print("⚠️  WhiteNoise not installed - static files will be served by web server")
else:
    print("📦 Using S3 storage - WhiteNoise middleware disabled")


MIDDLEWARE_LIST = list(MIDDLEWARE)
security_index = next(
    (i for i, mw in enumerate(MIDDLEWARE_LIST) if "SecurityMiddleware" in mw), 1
)


for i, mw in enumerate(reversed(PRE_SECURITY_MIDDLEWARE)):
    MIDDLEWARE_LIST.insert(security_index, mw)


MIDDLEWARE = PRE_SECURITY_MIDDLEWARE + MIDDLEWARE_LIST + PRODUCTION_MIDDLEWARE


REDIS_PRODUCTION_OPTIONS = {
    "CONNECTION_POOL_KWARGS": {
        "max_connections": 150,
        "retry_on_timeout": True,
        "socket_connect_timeout": 5,
        "socket_timeout": 10,
        "socket_keepalive": True,
        "socket_keepalive_options": {
            4: 1,
            5: 3,
            6: 5,
        },
        "health_check_interval": 300,
    },
    "IGNORE_EXCEPTIONS": True,
    "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
    "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
}


CACHES["default"]["OPTIONS"].update(REDIS_PRODUCTION_OPTIONS)
CACHES["sessions"]["OPTIONS"].update(REDIS_PRODUCTION_OPTIONS)


try:
    from redis.exceptions import ConnectionError, TimeoutError
except ImportError:
    ConnectionError = Exception
    TimeoutError = Exception


LOGGING = LOGGING_PROD


dictConfig(LOGGING)


Q_CLUSTER = {
    "name": "DjangORM-Prod",
    "workers": int(get_config_value("django_q.production.workers", 8)),
    "timeout": int(get_config_value("django_q.production.timeout", 60)),
    "retry": int(get_config_value("django_q.production.retry", 120)),
    "queue_limit": int(get_config_value("django_q.production.queue_limit", 200)),
    "bulk": 10,
    "orm": "default",
}
