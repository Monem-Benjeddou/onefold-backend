"""
Cache settings for the project.
"""

from ..config_loader import get_redis_config, get_environment
from redis.exceptions import ConnectionError, TimeoutError
import logging
import os

logger = logging.getLogger(__name__)


ENABLE_CACHE = os.environ.get("ENABLE_CACHE", "true").lower() in (
    "true",
    "1",
    "yes",
    "on",
)


log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
if log_level not in ["ERROR", "CRITICAL"]:
    logger.info(f"Cache functionality {'ENABLED' if ENABLE_CACHE else 'DISABLED'}")


redis_config = get_redis_config()
cache_config = redis_config["cache"]
session_config = redis_config["session"]
environment = get_environment()


use_do_redis = os.environ.get("USE_DO_REDIS", "false").lower() == "true"


def build_redis_url(config, db_number):
    """Build Redis URL for specific database number"""
    protocol = "rediss" if use_do_redis else "redis"

    if "USERNAME" in config and config.get("USERNAME") and config.get("PASSWORD"):
        return f"{protocol}://{config['USERNAME']}:{config['PASSWORD']}@{config['HOST']}:{config['PORT']}/{db_number}"
    elif config.get("PASSWORD"):
        return f"{protocol}://:{config['PASSWORD']}@{config['HOST']}:{config['PORT']}/{db_number}"
    else:
        return f"{protocol}://{config['HOST']}:{config['PORT']}/{db_number}"


cache_redis_url = build_redis_url(cache_config, cache_config["DB"])
session_redis_url = build_redis_url(cache_config, session_config["DB"])


REDIS_OPTIONS = {
    "CLIENT_CLASS": "django_redis.client.DefaultClient",
    "CONNECTION_POOL_KWARGS": {
        "max_connections": redis_config.get("CONNECTION_POOL_MAX_CONNECTIONS", 100),
        "retry_on_timeout": redis_config.get("RETRY_ON_TIMEOUT", True),
        "socket_connect_timeout": redis_config.get("SOCKET_CONNECT_TIMEOUT", 3),
        "socket_timeout": redis_config.get("SOCKET_TIMEOUT", 5),
        "socket_keepalive": redis_config.get("SOCKET_KEEPALIVE", True),
        "health_check_interval": redis_config.get("HEALTH_CHECK_INTERVAL", 10),
    },
    "IGNORE_EXCEPTIONS": True,
    "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
    "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
}


if use_do_redis:

    REDIS_OPTIONS["CONNECTION_POOL_KWARGS"].update(
        {
            "ssl": True,
            "ssl_cert_reqs": None,
            "ssl_check_hostname": False,
            "ssl_keyfile": None,
            "ssl_certfile": None,
            "ssl_ca_certs": None,
        }
    )
elif (
    environment == "production"
    and "USERNAME" in cache_config
    and cache_config["USERNAME"]
):

    REDIS_OPTIONS["CONNECTION_POOL_KWARGS"]["ssl_cert_reqs"] = None
    REDIS_OPTIONS["CONNECTION_POOL_KWARGS"]["ssl_check_hostname"] = False
    REDIS_OPTIONS["CONNECTION_POOL_KWARGS"]["ssl_keyfile"] = None
    REDIS_OPTIONS["CONNECTION_POOL_KWARGS"]["ssl_certfile"] = None
    REDIS_OPTIONS["CONNECTION_POOL_KWARGS"]["ssl_ca_certs"] = None

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": cache_redis_url,
        "OPTIONS": REDIS_OPTIONS,
        "KEY_PREFIX": "cache",
        "VERSION": 1,
        "TIMEOUT": 300,
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": session_redis_url,
        "OPTIONS": REDIS_OPTIONS,
        "KEY_PREFIX": "sessions",
        "VERSION": 1,
        "TIMEOUT": 86400,
    },
    "fallback": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "fallback-cache",
        "TIMEOUT": 300,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    },
    "db_fallback": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_table",
        "TIMEOUT": 300,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    },
}

CACHE_TTL = 60 * 15


REDIS_CONNECTION_POOL_KWARGS_DEFAULTS = {
    "max_connections": 50,
    "retry_on_timeout": True,
    "socket_connect_timeout": 5,
    "socket_timeout": 10,
    "socket_keepalive": True,
    "health_check_interval": 30,
}


if log_level not in ["ERROR", "CRITICAL"]:
    logger.info(f"Cache Redis URL configured: {cache_redis_url}")
    logger.info(f"Session Redis URL configured: {session_redis_url}")
if log_level not in ["ERROR", "CRITICAL"]:
    logger.info(
        f"Redis connection pool max connections: {REDIS_OPTIONS['CONNECTION_POOL_KWARGS']['max_connections']}"
    )
    logger.info(
        f"Redis socket timeout: {REDIS_OPTIONS['CONNECTION_POOL_KWARGS']['socket_timeout']}s"
    )
    logger.info(f"DigitalOcean Redis enabled: {use_do_redis}")

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "sessions"
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = CACHE_TTL
CACHE_MIDDLEWARE_KEY_PREFIX = ""


CACHE_CARDS_COMPONENTS = os.environ.get("CACHE_CARDS_COMPONENTS", "true").lower() in (
    "true",
    "1",
    "yes",
    "on",
)
CACHE_CARDS_STATS_TTL = int(os.environ.get("CACHE_CARDS_STATS_TTL", "300"))
CACHE_CARDS_METADATA_TTL = int(os.environ.get("CACHE_CARDS_METADATA_TTL", "3600"))
CACHE_CARDS_CONTENT_TYPE_TTL = int(
    os.environ.get("CACHE_CARDS_CONTENT_TYPE_TTL", "86400")
)

if log_level not in ["ERROR", "CRITICAL"]:
    logger.info(
        f"Cards component caching {'ENABLED' if CACHE_CARDS_COMPONENTS else 'DISABLED'}"
    )
    if CACHE_CARDS_COMPONENTS:
        logger.info(f"Cards stats cache TTL: {CACHE_CARDS_STATS_TTL}s")
        logger.info(f"Cards metadata cache TTL: {CACHE_CARDS_METADATA_TTL}s")
        logger.info(f"Cards ContentType cache TTL: {CACHE_CARDS_CONTENT_TYPE_TTL}s")
