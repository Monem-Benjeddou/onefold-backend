"""
Configuration loader for the project.

This module provides enterprise-grade functionality to load configuration from multiple sources:
1. Environment variables (for secrets and sensitive information) - HIGHEST PRIORITY
2. YAML configuration file (for non-sensitive settings) - LOWER PRIORITY
3. Secure defaults (for fallback values) - LOWEST PRIORITY

Security-first approach:
- All sensitive values MUST come from environment variables
- Configuration file is for non-sensitive structural settings only
- Clear separation between environments (development/production/testing)
- Type-safe configuration access with proper validation
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Type
from functools import lru_cache
import logging
from urllib.parse import urlparse
from django.core.exceptions import ImproperlyConfigured

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

T = TypeVar("T")
ConfigDict = Dict[str, Any]


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCKER_DIR = BASE_DIR / "docker"
CONFIG_FILE = DOCKER_DIR / "config.yml"


if DOTENV_AVAILABLE:

    env_value = os.environ.get("ENV", "1")
    if env_value == "0":
        env_file = BASE_DIR / ".env.production"
    elif env_value == "test" or "pytest" in os.environ.get("_", ""):
        env_file = BASE_DIR / ".env.testing"
    else:
        env_file = BASE_DIR / ".env"

    if env_file.exists():
        load_dotenv(env_file)
        if LOG_LEVEL not in ["ERROR", "CRITICAL"]:
            logger.info(f"✅ Environment variables loaded from {env_file}")
    else:

        fallback_env = BASE_DIR / ".env"
        if fallback_env.exists():
            load_dotenv(fallback_env)
            if LOG_LEVEL not in ["ERROR", "CRITICAL"]:
                logger.info(
                    f"✅ Environment variables loaded from {fallback_env} (fallback)"
                )
        else:

            if env_value == "0":
                if LOG_LEVEL not in ["ERROR", "CRITICAL"]:
                    logger.info(
                        f"📝 No .env file found - using environment variables from container"
                    )
            else:
                if LOG_LEVEL not in ["ERROR", "CRITICAL"]:
                    logger.info(
                        f"📝 No .env file found at {env_file} or {fallback_env}"
                    )
else:
    logger.warning(
        "⚠️  python-dotenv not available. Install it with: pip install python-dotenv"
    )


SECURE_SETTINGS = frozenset(
    {
        "SECRET_KEY",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
        "DATABASE_HOST",
        "NEON_DATABASE_URL",
        "REDIS_HOST",
        "REDIS_PASSWORD",
        "DO_REDIS_USERNAME",
        "DO_REDIS_PASSWORD",
        "DO_REDIS_HOST",
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
        "EMAIL_ACTIVATION_HOST",
        "EMAIL_ACTIVATION_PASSWORD",
        "EMAIL_NO_REPLY_PASSWORD",
        "ADMIN_EMAIL",
        "ADMIN_PASSWORD",
        "SENDGRID_API_KEY",
        "SENDGRID_SENDER",
        "MAILGUN_API_KEY",
        "MAILGUN_SENDER_DOMAIN",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_SID",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_API_KEY",
        "TWILIO_SMS_FROM_NUMBER",
        "TWILIO_VERIFY_SERVICE_SID",
        "VONAGE_API_KEY",
        "VONAGE_API_SECRET",
        "VONAGE_FROM",
        "NEONS_SMS_BASE_URL",
        "NEONS_SMS_CLIENT_ID",
        "NEONS_SMS_CLIENT_SECRET",
        "NEONS_SMS_TOKEN_CACHE_TTL",
        "OTP_DELIVERY_METHOD",
        "GOOGLE_ANALYTICS_TOKEN",
        "GOOGLE_ANALYTICS_CLIENT_ID",
        "GOOGLE_ANALYTICS_CLIENT_SECRET",
        "OPENAI_API_KEY",
        "WEBUI_SECRET_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "DO_SPACES_ACCESS_KEY_ID",
        "DO_SPACES_SECRET_ACCESS_KEY",
        "DO_SPACES_BUCKET_NAME",
        "DO_SPACES_ENDPOINT_URL",
        "DO_SPACES_REGION_NAME",
        "DO_SPACES_CUSTOM_DOMAIN",
        "DO_REDIS_HOST",
        "DO_REDIS_USERNAME",
        "DO_REDIS_PASSWORD",
        "DO_REDIS_PORT",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "REDIS_HOST",
        "REDIS_USERNAME",
        "REDIS_PASSWORD",
        "REDIS_PORT",
        "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY",
        "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET",
        "SOCIAL_AUTH_FACEBOOK_KEY",
        "SOCIAL_AUTH_FACEBOOK_SECRET",
        "FORGOT_PASSWORD_LINK",
        "MOYASAR_SECRET_KEY",
        "MOYASAR_PUBLISHABLE_KEY",
        "MOYASSAR_SECRET_TOKEN",
    }
)


def get_environment() -> str:
    """
    Detect current environment with secure fallback.

    Returns:
        str: Environment name ('development', 'production', 'testing')
    """

    if (
        os.environ.get("TESTING") == "true"
        or "pytest" in os.environ.get("_", "")
        or os.environ.get("PYTEST_CURRENT_TEST")
        or os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("testing")
    ):
        return "testing"

    env_value = os.environ.get("ENV", "1")
    if env_value == "0":
        return "production"
    elif env_value == "test":
        return "testing"
    else:
        return "development"


@lru_cache(maxsize=1)
def load_yaml_config() -> ConfigDict:
    """
    Load and cache configuration from YAML file with error handling.

    Returns:
        ConfigDict: The configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        if not CONFIG_FILE.exists():
            logger.warning(f"Configuration file not found: {CONFIG_FILE}")
            return {}

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}
            if LOG_LEVEL not in ["ERROR", "CRITICAL"]:
                logger.info(f"✅ Configuration loaded from {CONFIG_FILE}")
            return config

    except yaml.YAMLError as e:
        logger.error(f"❌ Failed to parse YAML configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error loading configuration: {e}")
        return {}


def get_secure_value(key: str, default: Any = None, required: bool = False) -> Any:
    """
    Get a secure value that MUST come from environment variables only.

    Args:
        key: The environment variable key
        default: Default value if not found
        required: Whether this value is required

    Returns:
        The secure value from environment

    Raises:
        ImproperlyConfigured: If required value is missing

    Security Note:
        This function will never check config files for security-critical values
    """

    if key.upper() not in SECURE_SETTINGS and key.upper() != "FIELD_ENCRYPTION_KEY":
        logger.warning(f"⚠️  Key '{key}' not in SECURE_SETTINGS - consider adding it")

    value = os.environ.get(key.upper(), default)

    if required and value is None:
        raise ImproperlyConfigured(
            f"Required secure setting '{key.upper()}' not found in environment variables. "
            f"Please set this value in your .env file or environment."
        )

    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get a boolean value from environment variables.

    Args:
        key: Environment variable key
        default: Default boolean value

    Returns:
        Boolean value
    """
    value = os.environ.get(key.upper(), str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """
    Get an integer value from environment variables.

    Args:
        key: Environment variable key
        default: Default integer value

    Returns:
        Integer value
    """
    try:
        return int(os.environ.get(key.upper(), str(default)))
    except ValueError:
        logger.warning(f"Invalid integer value for {key}, using default: {default}")
        return default


def get_env_list(
    key: str, default: List[str] = None, separator: str = ","
) -> List[str]:
    """
    Get a list value from environment variables.

    Args:
        key: Environment variable key
        default: Default list value
        separator: String separator for list items

    Returns:
        List of strings
    """
    if default is None:
        default = []

    value = os.environ.get(key.upper())
    if not value:
        return default

    return [item.strip() for item in value.split(separator) if item.strip()]


def get_config_value(
    key_path: Union[str, List[str]],
    default: Any = None,
    environment: Optional[str] = None,
    required: bool = False,
) -> Any:
    """
    Get configuration value with environment-aware fallback chain.

    Priority order:
    1. Environment variables (for secure settings)
    2. Environment-specific config (config.yml)
    3. General config (config.yml)
    4. Default value

    Args:
        key_path: Dot-separated path or list of keys
        default: Default value if not found
        environment: Target environment (auto-detected if None)
        required: Whether this setting is required

    Returns:
        Configuration value

    Raises:
        ValueError: If required setting is missing
    """
    if environment is None:
        environment = get_environment()

    if isinstance(key_path, str):
        keys = key_path.split(".")
    else:
        keys = list(key_path)

    key_name = keys[-1].upper() if keys else ""
    if key_name in SECURE_SETTINGS:
        value = get_secure_value(key_name, default)
        if required and value is None:
            raise ValueError(
                f"Required secure setting '{key_name}' not found in environment"
            )
        return value

    config = load_yaml_config()

    env_keys = keys[:-1] + [environment, keys[-1]]
    value = _get_nested_value(config, env_keys)
    if value is not None:
        return value

    value = _get_nested_value(config, keys)
    if value is not None:
        return value

    env_var = "_".join(k.upper() for k in keys)
    env_value = os.environ.get(env_var)
    if env_value is not None:
        return env_value

    if required and default is None:
        raise ValueError(f"Required setting '{'.'.join(keys)}' not found")

    return default


def _get_nested_value(config: ConfigDict, keys: List[str]) -> Any:
    """
    Safely get nested value from configuration dictionary.

    Args:
        config: Configuration dictionary
        keys: List of nested keys

    Returns:
        Value if found, None otherwise
    """
    try:
        value = config
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value
    except (KeyError, TypeError):
        return None


def get_environment_config() -> ConfigDict:
    """Get current environment configuration."""
    env = get_environment()
    return get_config_value(f"environment.{env}", {}, env)


def parse_database_url(database_url: str) -> ConfigDict:
    """
    Parse a database URL into Django database configuration components.

    Supports PostgreSQL URLs in the format:
    postgresql://user:password@host:port/database?sslmode=require&channel_binding=require
    """
    if not database_url:
        return {}

    try:
        parsed = urlparse(database_url)

        if not parsed.scheme or parsed.scheme not in ["postgresql", "postgres"]:
            logger.warning(f"Invalid database URL scheme: {parsed.scheme}")
            return {}

        if not parsed.hostname:
            logger.warning("Database URL missing hostname")
            return {}

        from urllib.parse import unquote

        username = unquote(parsed.username) if parsed.username else ""
        password = unquote(parsed.password) if parsed.password else ""

        config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/") if parsed.path else "",
            "USER": username,
            "PASSWORD": password,
            "HOST": parsed.hostname or "",
            "PORT": parsed.port or 5432,
        }

        options = {}
        if parsed.query:
            from urllib.parse import parse_qs

            query_params = parse_qs(parsed.query)

            if "sslmode" in query_params:
                sslmode = query_params["sslmode"][0]
                if sslmode == "require":
                    options["sslmode"] = "require"

            if "channel_binding" in query_params:
                channel_binding = query_params["channel_binding"][0]
                if channel_binding == "require":
                    options["channel_binding"] = "require"

        if options:
            config["OPTIONS"] = options

        return config

    except Exception as e:
        logger.error(f"Failed to parse database URL: {e}")
        return {}


def get_database_config() -> ConfigDict:
    """Get database configuration for current environment."""
    env = get_environment()
    base_config = get_config_value("database", {}, env)
    env_config = get_config_value(f"database.{env}", {}, env)

    if env == "testing":
        import tempfile
        import uuid
        import os

        worker_id = os.environ.get(
            "PYTEST_XDIST_WORKER", f"main_{uuid.uuid4().hex[:8]}"
        )
        temp_dir = tempfile.gettempdir()
        db_file = f"{temp_dir}/test_db_{worker_id}.sqlite3"

        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": db_file,
            "CONN_MAX_AGE": 0,
            "ATOMIC_REQUESTS": False,
            "OPTIONS": {
                "timeout": 30,
                "check_same_thread": False,
                "isolation_level": None,
            },
            "TEST": {
                "NAME": db_file,
                "OPTIONS": {
                    "timeout": 30,
                    "check_same_thread": False,
                    "isolation_level": None,
                },
            },
        }

    neon_url = get_secure_value("NEON_DATABASE_URL")
    if neon_url:
        if LOG_LEVEL not in ["ERROR", "CRITICAL"]:
            logger.info("🚀 Using Neon.com serverless database configuration")
        neon_config = parse_database_url(neon_url)
        if neon_config:

            neon_config.update(
                {
                    "ATOMIC_REQUESTS": env_config.get(
                        "atomic_requests", base_config.get("atomic_requests", True)
                    ),
                    "CONN_MAX_AGE": env_config.get(
                        "conn_max_age", base_config.get("conn_max_age", 60)
                    ),
                }
            )

            if "OPTIONS" not in neon_config:
                neon_config["OPTIONS"] = {}
            neon_config["OPTIONS"].update(
                {
                    "connect_timeout": 10,
                    "sslmode": "require",
                }
            )

            test_db_name = env_config.get(
                "test_database_name", base_config.get("test_database_name")
            )
            if test_db_name:
                neon_config["TEST"] = {"NAME": test_db_name}
            else:

                pass

            return neon_config

    test_db_name = env_config.get(
        "test_database_name", base_config.get("test_database_name")
    )

    db_options = env_config.get("options", base_config.get("options", {}))

    config = {
        "NAME": get_secure_value("DATABASE_NAME", "postgres"),
        "USER": get_secure_value("DATABASE_USER", "postgres"),
        "PASSWORD": get_secure_value("DATABASE_PASSWORD", "postgres"),
        "HOST": get_secure_value(
            "DATABASE_HOST",
            env_config.get("host", base_config.get("host", "localhost")),
        ),
        "PORT": get_env_int(
            "DATABASE_INTERNAL_PORT",
            env_config.get("port", base_config.get("port", 5432)),
        ),
        "ATOMIC_REQUESTS": env_config.get(
            "atomic_requests", base_config.get("atomic_requests", True)
        ),
        "CONN_MAX_AGE": env_config.get(
            "conn_max_age", base_config.get("conn_max_age", 60)
        ),
        "CONN_HEALTH_CHECKS": env_config.get(
            "conn_health_checks", base_config.get("conn_health_checks", True)
        ),
        "TEST": {"NAME": test_db_name} if test_db_name else {},
    }

    if db_options:
        config["OPTIONS"] = db_options

    return config


def get_redis_config() -> ConfigDict:
    """Get Redis configuration for current environment."""
    env = get_environment()
    redis_config = get_config_value("redis", {}, env)
    env_redis = get_config_value(f"redis.{env}", {}, env)

    use_do_redis = get_env_bool("USE_DO_REDIS", False)
    if use_do_redis:
        if LOG_LEVEL not in ["ERROR", "CRITICAL"]:
            logger.info("🚀 Using DigitalOcean managed Redis service")

        do_redis_host = get_secure_value("DO_REDIS_HOST")
        do_redis_port = get_env_int("DO_REDIS_PORT", 25061)
        do_redis_username = get_secure_value("DO_REDIS_USERNAME", "default")
        do_redis_password = get_secure_value("DO_REDIS_PASSWORD")

        if not do_redis_host or not do_redis_password:
            logger.error("❌ DigitalOcean Redis credentials not properly configured")
            raise ImproperlyConfigured(
                "DigitalOcean Redis is enabled but credentials are missing. "
                "Please set DO_REDIS_HOST and DO_REDIS_PASSWORD environment variables."
            )

        return {
            "HOST": do_redis_host,
            "PORT": do_redis_port,
            "USERNAME": do_redis_username,
            "PASSWORD": do_redis_password,
            "cache": {
                "HOST": do_redis_host,
                "PORT": do_redis_port,
                "DB": 0,
                "USERNAME": do_redis_username,
                "PASSWORD": do_redis_password,
            },
            "celery": {
                "BROKER_DB": 0,
                "RESULT_DB": 0,
            },
            "session": {
                "DB": 0,
            },
        }

    password = get_secure_value("REDIS_PASSWORD")
    username = get_secure_value("REDIS_USERNAME")
    host = get_secure_value(
        "REDIS_HOST", env_redis.get("host", redis_config.get("host", "localhost"))
    )
    port = get_env_int(
        "REDIS_PORT", env_redis.get("port", redis_config.get("port", 6379))
    )

    if password == "":
        password = None
    if username == "":
        username = None

    config = {
        "HOST": host,
        "PORT": port,
        "PASSWORD": password,
        "CONNECTION_POOL_MAX_CONNECTIONS": get_env_int(
            "REDIS_MAX_CONNECTIONS",
            env_redis.get(
                "connection_pool_max_connections",
                redis_config.get("connection_pool_max_connections", 100),
            ),
        ),
        "SOCKET_CONNECT_TIMEOUT": get_env_int(
            "REDIS_CONNECT_TIMEOUT",
            env_redis.get(
                "socket_connect_timeout", redis_config.get("socket_connect_timeout", 2)
            ),
        ),
        "SOCKET_TIMEOUT": get_env_int(
            "REDIS_SOCKET_TIMEOUT",
            env_redis.get("socket_timeout", redis_config.get("socket_timeout", 5)),
        ),
        "RETRY_ON_TIMEOUT": get_env_bool(
            "REDIS_RETRY_ON_TIMEOUT",
            env_redis.get(
                "retry_on_timeout", redis_config.get("retry_on_timeout", True)
            ),
        ),
        "HEALTH_CHECK_INTERVAL": get_env_int(
            "REDIS_HEALTH_CHECK_INTERVAL",
            env_redis.get(
                "health_check_interval", redis_config.get("health_check_interval", 10)
            ),
        ),
        "SOCKET_KEEPALIVE": get_env_bool(
            "REDIS_SOCKET_KEEPALIVE",
            env_redis.get(
                "socket_keepalive", redis_config.get("socket_keepalive", True)
            ),
        ),
        "cache": {
            "HOST": host,
            "PORT": port,
            "DB": get_env_int(
                "REDIS_CACHE_DB",
                env_redis.get("cache_db", redis_config.get("cache_db", 1)),
            ),
            "PASSWORD": password,
        },
        "celery": {
            "BROKER_DB": get_env_int(
                "REDIS_CELERY_BROKER_DB",
                env_redis.get(
                    "celery_broker_db", redis_config.get("celery_broker_db", 0)
                ),
            ),
            "RESULT_DB": get_env_int(
                "REDIS_CELERY_RESULT_DB",
                env_redis.get(
                    "celery_result_db", redis_config.get("celery_result_db", 0)
                ),
            ),
        },
        "session": {
            "DB": get_env_int(
                "REDIS_SESSION_DB",
                env_redis.get("session_db", redis_config.get("session_db", 2)),
            ),
        },
    }

    if username is not None:
        config["USERNAME"] = username
        config["cache"]["USERNAME"] = username

    return config


def get_email_config() -> ConfigDict:
    """Get email configuration for current environment."""
    env = get_environment()
    email_config = get_config_value("email", {}, env)
    env_email = get_config_value(f"email.{env}", {}, env)

    return {
        "HOST": env_email.get("host", email_config.get("host", "localhost")),
        "PORT": int(env_email.get("port", email_config.get("port", 587))),
        "USE_TLS": env_email.get("use_tls", email_config.get("use_tls", False)),
        "USE_SSL": env_email.get("use_ssl", email_config.get("use_ssl", False)),
        "HOST_USER": get_secure_value("EMAIL_HOST_USER", ""),
        "HOST_PASSWORD": get_secure_value("EMAIL_HOST_PASSWORD", ""),
        "DEFAULT_FROM": env_email.get(
            "default_from", email_config.get("default_from", "noreply@localhost")
        ),
        "ACTIVATION_HOST": get_secure_value("EMAIL_ACTIVATION_HOST", ""),
        "ACTIVATION_PASSWORD": get_secure_value("EMAIL_ACTIVATION_PASSWORD", ""),
        "ACTIVATION_PORT": int(
            env_email.get("activation_port", email_config.get("activation_port", 465))
        ),
        "ACTIVATION_USE_TLS": env_email.get(
            "activation_use_tls", email_config.get("activation_use_tls", False)
        ),
        "ACTIVATION_USE_SSL": env_email.get(
            "activation_use_ssl", email_config.get("activation_use_ssl", True)
        ),
        "NO_REPLY_PORT": int(
            env_email.get("no_reply_port", email_config.get("no_reply_port", 465))
        ),
        "NO_REPLY_USE_TLS": env_email.get(
            "no_reply_use_tls", email_config.get("no_reply_use_tls", False)
        ),
        "NO_REPLY_USE_SSL": env_email.get(
            "no_reply_use_ssl", email_config.get("no_reply_use_ssl", True)
        ),
        "MAILGUN_API_KEY": get_secure_value("MAILGUN_API_KEY", ""),
        "MAILGUN_SENDER_DOMAIN": get_secure_value("MAILGUN_SENDER_DOMAIN", ""),
        "SENDGRID_API_KEY": get_secure_value("SENDGRID_API_KEY", ""),
        "SENDGRID_SENDER": get_secure_value("SENDGRID_SENDER", ""),
        "SENDGRID_SANDBOX_MODE_IN_DEBUG": env_email.get(
            "sendgrid_sandbox_mode_in_debug",
            email_config.get("sendgrid_sandbox_mode_in_debug", False),
        ),
        "SENDGRID_ECHO_TO_STDOUT": env_email.get(
            "sendgrid_echo_to_stdout",
            email_config.get("sendgrid_echo_to_stdout", False),
        ),
    }


def get_celery_config() -> ConfigDict:
    """Get Celery configuration for current environment."""
    env = get_environment()
    celery_config = get_config_value("celery", {}, env)
    env_celery = get_config_value(f"celery.{env}", {}, env)

    if env == "testing":
        return {
            "BROKER_URL": "memory://",
            "RESULT_BACKEND": "cache+memory://",
            "TIMEZONE": celery_config.get("timezone", "UTC"),
            "TASK_TIME_LIMIT": int(celery_config.get("task_time_limit", 3600)),
            "WORKER_DISABLE_RATE_LIMITS": celery_config.get(
                "worker_disable_rate_limits", True
            ),
            "WORKER_PREFETCH_MULTIPLIER": int(
                celery_config.get("worker_prefetch_multiplier", 1)
            ),
            "WORKER_MAX_TASKS_PER_CHILD": int(
                celery_config.get("worker_max_tasks_per_child", 1000)
            ),
            "WORKER_CONCURRENCY": int(celery_config.get("worker_concurrency", 4)),
            "TASK_TRACK_STARTED": celery_config.get("task_track_started", True),
            "WORKER_STATE_DB": celery_config.get(
                "worker_state_db", "/tmp/celery_worker_state"
            ),
            "WORKER_MAX_MEMORY_PER_CHILD": int(
                celery_config.get("worker_max_memory_per_child", 262144)
            ),
            "TASK_ALWAYS_EAGER": True,
            "TASK_EAGER_PROPAGATES": True,
            "BROKER_CONNECTION_RETRY_ON_STARTUP": False,
            "BROKER_CONNECTION_MAX_RETRIES": 0,
        }

    redis_config = get_redis_config()
    use_do_redis = get_env_bool("USE_DO_REDIS", False)

    if use_do_redis:

        if (
            "USERNAME" in redis_config
            and redis_config["USERNAME"]
            and redis_config["PASSWORD"]
        ):
            broker_url = f"rediss://{redis_config['USERNAME']}:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['BROKER_DB']}?ssl_cert_reqs=CERT_REQUIRED"
            result_backend = f"rediss://{redis_config['USERNAME']}:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['RESULT_DB']}?ssl_cert_reqs=CERT_REQUIRED"
        elif redis_config["PASSWORD"]:
            broker_url = f"rediss://:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['BROKER_DB']}?ssl_cert_reqs=CERT_REQUIRED"
            result_backend = f"rediss://:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['RESULT_DB']}?ssl_cert_reqs=CERT_REQUIRED"
        else:
            broker_url = f"rediss://{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['BROKER_DB']}?ssl_cert_reqs=CERT_REQUIRED"
            result_backend = f"rediss://{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['RESULT_DB']}?ssl_cert_reqs=CERT_REQUIRED"
    else:

        if (
            "USERNAME" in redis_config
            and redis_config["USERNAME"]
            and redis_config["PASSWORD"]
        ):
            broker_url = f"redis://{redis_config['USERNAME']}:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['BROKER_DB']}"
            result_backend = f"redis://{redis_config['USERNAME']}:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['RESULT_DB']}"
        elif redis_config["PASSWORD"]:
            broker_url = f"redis://:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['BROKER_DB']}"
            result_backend = f"redis://:{redis_config['PASSWORD']}@{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['RESULT_DB']}"
        else:
            broker_url = f"redis://{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['BROKER_DB']}"
            result_backend = f"redis://{redis_config['HOST']}:{redis_config['PORT']}/{redis_config['celery']['RESULT_DB']}"

    return {
        "BROKER_URL": broker_url,
        "RESULT_BACKEND": result_backend,
        "TIMEZONE": celery_config.get("timezone", "UTC"),
        "TASK_TIME_LIMIT": int(celery_config.get("task_time_limit", 3600)),
        "WORKER_DISABLE_RATE_LIMITS": celery_config.get(
            "worker_disable_rate_limits", True
        ),
        "WORKER_PREFETCH_MULTIPLIER": int(
            celery_config.get("worker_prefetch_multiplier", 1)
        ),
        "WORKER_MAX_TASKS_PER_CHILD": int(
            celery_config.get("worker_max_tasks_per_child", 1000)
        ),
        "WORKER_CONCURRENCY": int(celery_config.get("worker_concurrency", 4)),
        "TASK_TRACK_STARTED": celery_config.get("task_track_started", True),
        "WORKER_STATE_DB": celery_config.get(
            "worker_state_db", "/tmp/celery_worker_state"
        ),
        "WORKER_MAX_MEMORY_PER_CHILD": int(
            celery_config.get("worker_max_memory_per_child", 262144)
        ),
        "TASK_ALWAYS_EAGER": env_celery.get("task_always_eager", False),
        "TASK_EAGER_PROPAGATES": env_celery.get("task_eager_propagates", True),
        "BROKER_CONNECTION_RETRY_ON_STARTUP": env_celery.get(
            "broker_connection_retry_on_startup", True
        ),
        "BROKER_CONNECTION_MAX_RETRIES": int(
            env_celery.get("broker_connection_max_retries", 10)
        ),
    }


def get_api_config() -> ConfigDict:
    """Get API configuration for current environment."""
    env = get_environment()
    api_config = get_config_value("api", {}, env)
    env_api = get_config_value(f"api.{env}", {}, env)

    return {
        "PORT": int(
            os.environ.get(
                "API_PORT", env_api.get("port", api_config.get("port", 8000))
            )
        ),
        "BASE_URL": os.environ.get(
            "API_BASE_URL",
            env_api.get(
                "base_url", api_config.get("base_url", "http://localhost:8009")
            ),
        ),
        "WEBSOCKET_URL": env_api.get(
            "websocket_url", api_config.get("websocket_url", "ws://localhost:8009")
        ),
    }


def get_frontend_config() -> ConfigDict:
    """Get frontend configuration for current environment."""
    env = get_environment()
    frontend_config = get_config_value("frontend", {}, env)
    env_frontend = get_config_value(f"frontend.{env}", {}, env)
    ui_urls = get_config_value("frontend.ui_urls", {}, env)
    env_ui_urls = get_config_value(f"frontend.ui_urls.{env}", {}, env)

    return {
        "PORT": int(
            os.environ.get(
                "FRONTEND_PORT",
                env_frontend.get("port", frontend_config.get("port", 5173)),
            )
        ),
        "URL": os.environ.get(
            "FRONTEND_URL",
            env_frontend.get(
                "url", frontend_config.get("url", "http://localhost:5173")
            ),
        ),
        "BUILD_TARGET": os.environ.get(
            "FRONTEND_TARGET",
            env_frontend.get(
                "build_target", frontend_config.get("build_target", "development")
            ),
        ),
        "VITE_API_URL": os.environ.get(
            "VITE_API_URL",
            env_frontend.get(
                "vite_api_url",
                frontend_config.get("vite_api_url", "http://localhost:8009"),
            ),
        ),
        "UI_URLS": {
            "CANDIDATE": os.environ.get(
                "UI_BASE_URL_CANDIDATE",
                env_ui_urls.get("candidate", ui_urls.get("candidate")),
            ),
            "JURY": os.environ.get(
                "UI_BASE_URL_JURY", env_ui_urls.get("jury", ui_urls.get("jury"))
            ),
            "ADMIN": os.environ.get(
                "UI_BASE_URL_ADMIN", env_ui_urls.get("admin", ui_urls.get("admin"))
            ),
        },
    }


def get_security_config() -> ConfigDict:
    """Get security configuration."""
    security_config = get_config_value("security", {})

    return {
        "BROWSER_XSS_FILTER": os.environ.get(
            "SECURE_BROWSER_XSS_FILTER",
            str(security_config.get("browser_xss_filter", True)),
        ).lower()
        in ("true", "1", "t"),
        "CONTENT_TYPE_NOSNIFF": os.environ.get(
            "SECURE_CONTENT_TYPE_NOSNIFF",
            str(security_config.get("content_type_nosniff", True)),
        ).lower()
        in ("true", "1", "t"),
        "HSTS_INCLUDE_SUBDOMAINS": os.environ.get(
            "SECURE_HSTS_INCLUDE_SUBDOMAINS",
            str(security_config.get("hsts_include_subdomains", True)),
        ).lower()
        in ("true", "1", "t"),
        "HSTS_PRELOAD": os.environ.get(
            "SECURE_HSTS_PRELOAD", str(security_config.get("hsts_preload", True))
        ).lower()
        in ("true", "1", "t"),
        "SSL_HOST": os.environ.get("SECURE_SSL_HOST"),
        "PROXY_SSL_HEADER": tuple(
            security_config.get("proxy_ssl_header", ["HTTP_X_FORWARDED_PROTO", "https"])
        ),
        "PASSWORD_MIN_LENGTH": security_config.get("password_validators", {}).get(
            "min_length", 8
        ),
    }


def get_aws_config() -> ConfigDict:
    """Get AWS/DigitalOcean Spaces configuration."""
    storage_config = get_config_value("storage", {})

    access_key = get_secure_value("DO_SPACES_ACCESS_KEY_ID", "") or get_secure_value(
        "AWS_ACCESS_KEY_ID", ""
    )
    secret_key = get_secure_value(
        "DO_SPACES_SECRET_ACCESS_KEY", ""
    ) or get_secure_value("AWS_SECRET_ACCESS_KEY", "")
    bucket_name = get_secure_value("DO_SPACES_BUCKET_NAME", "") or storage_config.get(
        "bucket_name", ""
    )

    region = get_secure_value("DO_SPACES_REGION_NAME", "") or storage_config.get(
        "region", "us-east-1"
    )

    return {
        "ACCESS_KEY_ID": access_key,
        "SECRET_ACCESS_KEY": secret_key,
        "STORAGE_BUCKET_NAME": bucket_name,
        "S3_REGION_NAME": region,
        "S3_SIGNATURE_VERSION": storage_config.get("signature_version", "s3v4"),
        "S3_FILE_OVERWRITE": storage_config.get("file_overwrite", False),
        "DEFAULT_ACL": storage_config.get("default_acl"),
        "S3_VERIFY": storage_config.get("verify", True),
    }


def get_calculator_config() -> ConfigDict:
    """Get calculator configuration limits."""
    calculator_config = get_config_value("calculators", {})

    return {
        "MACRO": calculator_config.get("macro", {}),
        "WATER_INTAKE": calculator_config.get("water_intake", {}),
        "BMI": calculator_config.get("bmi", {}),
    }
