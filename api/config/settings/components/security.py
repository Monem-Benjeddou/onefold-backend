"""
Security settings for the Django project.

Enterprise-grade security configuration with:
- Environment-aware settings (dev/prod/test)
- Zero duplication across environments
- Secure defaults with proper fallbacks
- Full integration with centralized config system
"""

import os
from datetime import timedelta
from typing import Dict, Any, List, Tuple

from ..config_loader import (
    get_config_value,
    get_environment,
    get_security_config,
    get_secure_value,
)


ENVIRONMENT = get_environment()


security_config = get_security_config()


SECRET_KEY = get_secure_value(
    "SECRET_KEY", "django-insecure-this-should-be-changed-in-production"
)


CSRF_COOKIE_SECURE = get_config_value(
    f"environment.{ENVIRONMENT}.secure.cookie_secure",
    default=ENVIRONMENT == "production",
)

CSRF_COOKIE_HTTPONLY = get_config_value("csrf.cookie_httponly", default=True)

CSRF_COOKIE_SAMESITE = get_config_value("csrf.cookie_samesite", default="Lax")

CSRF_TRUSTED_ORIGINS = get_config_value(
    f"environment.{ENVIRONMENT}.csrf.trusted_origins", default=[]
)


SESSION_COOKIE_SECURE = get_config_value(
    f"environment.{ENVIRONMENT}.secure.cookie_secure",
    default=ENVIRONMENT == "production",
)

SESSION_COOKIE_HTTPONLY = get_config_value("session.cookie_httponly", default=True)

SESSION_COOKIE_SAMESITE = get_config_value("session.cookie_samesite", default="Lax")

SESSION_COOKIE_AGE = int(get_config_value("session.cookie_age", default=1209600))


SECURE_BROWSER_XSS_FILTER = security_config["BROWSER_XSS_FILTER"]
SECURE_CONTENT_TYPE_NOSNIFF = security_config["CONTENT_TYPE_NOSNIFF"]
SECURE_HSTS_INCLUDE_SUBDOMAINS = security_config["HSTS_INCLUDE_SUBDOMAINS"]
SECURE_HSTS_PRELOAD = security_config["HSTS_PRELOAD"]

SECURE_HSTS_SECONDS = int(
    get_config_value(
        f"environment.{ENVIRONMENT}.secure.hsts_seconds",
        default=31536000 if ENVIRONMENT == "production" else 0,
    )
)

SECURE_SSL_REDIRECT = get_config_value(
    f"environment.{ENVIRONMENT}.secure.ssl_redirect",
    default=ENVIRONMENT == "production",
)

SECURE_SSL_HOST = security_config["SSL_HOST"]
SECURE_PROXY_SSL_HEADER = security_config["PROXY_SSL_HEADER"]
SECURE_REDIRECT_EXEMPT: List[str] = []


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": security_config["PASSWORD_MIN_LENGTH"],
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]


jwt_config = get_config_value("jwt", {})


jwt_access_lifetime = jwt_config.get("access_token_lifetime_minutes", 30)

jwt_refresh_lifetime = jwt_config.get("refresh_token_lifetime_days", 7)


jwt_rotate_tokens = jwt_config.get("rotate_refresh_tokens", True)

jwt_blacklist_after_rotation = jwt_config.get("blacklist_after_rotation", True)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=jwt_access_lifetime),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=jwt_refresh_lifetime),
    "ROTATE_REFRESH_TOKENS": jwt_rotate_tokens,
    "BLACKLIST_AFTER_ROTATION": jwt_blacklist_after_rotation,
    "ALGORITHM": jwt_config.get("algorithm", "HS256"),
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": tuple(jwt_config.get("auth_header_types", ["Bearer"])),
    "USER_ID_FIELD": jwt_config.get("user_id_field", "id"),
    "USER_ID_CLAIM": jwt_config.get("user_id_claim", "user_id"),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": jwt_config.get("token_type_claim", "token_type"),
    "JTI_CLAIM": jwt_config.get("jti_claim", "jti"),
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=jwt_access_lifetime),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=jwt_refresh_lifetime),
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "UPDATE_LAST_LOGIN": True,
}


if ENVIRONMENT == "production":
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
else:
    X_FRAME_OPTIONS = "SAMEORIGIN"


cors_config = get_config_value("cors", {})

CORS_ALLOW_ALL_ORIGINS = get_config_value(
    f"environment.{ENVIRONMENT}.cors.allow_all_origins",
    default=ENVIRONMENT != "production",
)

CORS_ALLOWED_ORIGINS = get_config_value(
    f"environment.{ENVIRONMENT}.cors.allowed_origins", default=[]
)

CORS_ALLOW_CREDENTIALS = cors_config.get("allow_credentials", True)

CORS_ALLOW_METHODS = cors_config.get(
    "allow_methods",
    [
        "DELETE",
        "GET",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT",
    ],
)

CORS_ALLOW_HEADERS = cors_config.get(
    "allow_headers",
    [
        "accept",
        "accept-encoding",
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-requested-with",
    ],
)


if ENVIRONMENT == "production":
    CORS_ORIGIN_WHITELIST = get_config_value(
        f"environment.{ENVIRONMENT}.cors.allowed_origins", default=[]
    )

    CORS_ALLOWED_ORIGIN_REGEXES: List[str] = []

else:

    CORS_ORIGIN_WHITELIST = get_config_value(
        f"environment.{ENVIRONMENT}.cors.allowed_origins",
        default=[
            "http://localhost:3000",
            "http://localhost:3018",
            "http://localhost:5173",
            "http://localhost:8009",
        ],
    )


rate_limiter_config = get_config_value("rate_limiter", {})

RATE_LIMITER_ENABLED = rate_limiter_config.get("enabled", ENVIRONMENT == "production")

RATE_LIMIT_DEFAULT = rate_limiter_config.get("default_rate", "100/day")

RATE_LIMIT_SENSITIVE = rate_limiter_config.get("sensitive_rate", "10/minute")


DB_CREDENTIAL_ROTATION_INTERVAL = 3600
DB_SSL_CERT_PATH = os.environ.get("DB_SSL_CERT_PATH")
DB_SSL_KEY_PATH = os.environ.get("DB_SSL_KEY_PATH")
DB_SSL_ROOT_CERT_PATH = os.environ.get("DB_SSL_ROOT_CERT_PATH")


MAX_TRANSACTION_TIME_SECONDS = 300
DEFAULT_ISOLATION_LEVEL = "READ_COMMITTED"
MAX_CONCURRENT_DB_OPERATIONS = 10


DATABASE_SECURITY_OPTIONS = {
    "connect_timeout": 10,
    "application_name": f"kolct_api_{ENVIRONMENT}",
    "sslmode": "require" if ENVIRONMENT == "production" else "prefer",
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 5,
    "server_side_binding": True,
    "isolation_level": 2,
}


DATABASE_CONNECTION_POOLING_SECURE = {
    "POOL_SIZE": 20,
    "MAX_OVERFLOW": 10,
    "POOL_TIMEOUT": 30,
    "POOL_RECYCLE": 3600,
    "POOL_PRE_PING": True,
    "POOL_RESET_ON_RETURN": "commit",
}


EXPORT_RATE_LIMITS = {
    "admin": {"rate": 10, "period": 300},
    "salesman": {"rate": 8, "period": 300},
    "issuer": {"rate": 5, "period": 300},
    "manufacturer": {"rate": 3, "period": 300},
    "user": {"rate": 1, "period": 600},
}


EXPORT_SIZE_LIMITS = {
    "admin": 50000,
    "salesman": 25000,
    "issuer": 10000,
    "manufacturer": 5000,
    "user": 1000,
}


EXPORT_RESTRICTED_FIELDS = {
    "private_key",
    "password",
    "secret",
    "token",
    "api_key",
    "ssn",
    "social_security",
    "credit_card",
    "bank_account",
    "internal_notes",
    "admin_notes",
    "debug_info",
}


EXPORT_AUDIT_SETTINGS = {
    "LOG_ALL_EXPORTS": True,
    "LOG_LARGE_EXPORTS_THRESHOLD": 5000,
    "LOG_FREQUENT_EXPORTS_THRESHOLD": 5,
    "LOG_SENSITIVE_FIELD_ACCESS": True,
}


TEST_DB_ENCRYPTION_ENABLED = True
TEST_MEMORY_THRESHOLD_MB = 512
TEST_CLEANUP_INTERVAL = 10
TEST_DB_ISOLATION_ENABLED = True


TEST_CREDENTIAL_PATTERNS = {
    "SECRET_KEY": "test-secret-key-not-for-production-",
    "API_KEY_PATTERN": "test-api-key-",
    "TOKEN_PATTERN": "test-token-",
}


PRODUCTION_ENV_VARS_BLOCKED = {
    "NEON_DATABASE_URL",
    "PRODUCTION_DATABASE_URL",
    "PROD_DATABASE_URL",
    "LIVE_DATABASE_URL",
    "SENDGRID_API_KEY",
    "TWILIO_AUTH_TOKEN",
    "STRIPE_SECRET_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "DO_SPACES_SECRET_ACCESS_KEY",
    "PRODUCTION_SECRET_KEY",
    "LIVE_SECRET_KEY",
}


FIELD_ENCRYPTION_SETTINGS = {
    "ALGORITHM": "AES-256-GCM",
    "KEY_ROTATION_INTERVAL_DAYS": 90,
    "BACKUP_KEY_COUNT": 3,
    "ENCRYPTION_KEY_SOURCE": "environment",
}


ENVELOPE_ENCRYPTION_SETTINGS = {
    "ENABLED": True,
    "DEK_ALGORITHM": "AES-256-GCM",
    "KEK_ALGORITHM": "RSA-4096",
    "KEY_HIERARCHY_LEVELS": 2,
}


RBAC_PERMISSIONS = {
    "admin": {
        "can_export_all": True,
        "can_view_sensitive_fields": True,
        "can_modify_security_settings": True,
        "can_access_audit_logs": True,
        "max_export_records": 50000,
    },
    "salesman": {
        "can_export_all": True,
        "can_view_sensitive_fields": False,
        "can_modify_security_settings": False,
        "can_access_audit_logs": False,
        "max_export_records": 25000,
    },
    "issuer": {
        "can_export_all": False,
        "can_view_sensitive_fields": False,
        "can_modify_security_settings": False,
        "can_access_audit_logs": False,
        "max_export_records": 10000,
        "data_scope": "own_issued_cards",
    },
    "manufacturer": {
        "can_export_all": False,
        "can_view_sensitive_fields": False,
        "can_modify_security_settings": False,
        "can_access_audit_logs": False,
        "max_export_records": 5000,
        "data_scope": "own_manufactured_cards",
    },
    "user": {
        "can_export_all": False,
        "can_view_sensitive_fields": False,
        "can_modify_security_settings": False,
        "can_access_audit_logs": False,
        "max_export_records": 1000,
        "data_scope": "own_data_only",
    },
}


CONCURRENT_OPERATION_LIMITS = {
    "admin": 10,
    "salesman": 8,
    "issuer": 5,
    "manufacturer": 3,
    "user": 2,
}


OPERATION_LOCK_SETTINGS = {
    "DEFAULT_TIMEOUT_SECONDS": 300,
    "MAX_LOCK_DURATION_SECONDS": 1800,
    "DEADLOCK_DETECTION_INTERVAL": 30,
}


ERROR_SANITIZATION_PATTERNS = [
    r'password[=:]\s*[\'"][^\'"]*[\'"]',
    r'user[=:]\s*[\'"][^\'"]*[\'"]',
    r'host[=:]\s*[\'"][^\'"]*[\'"]',
    r"port[=:]\s*\d+",
    r'database[=:]\s*[\'"][^\'"]*[\'"]',
    r"DETAIL:\s*.*",
    r"HINT:\s*.*",
    r"CONTEXT:\s*.*",
    r"connection string.*",
    r"server.*host.*",
]


SECURITY_ALERT_THRESHOLDS = {
    "FAILED_LOGINS_PER_IP": 10,
    "FAILED_LOGINS_PER_USER": 5,
    "LARGE_EXPORT_THRESHOLD": 10000,
    "RAPID_EXPORT_ATTEMPTS": 5,
    "PERMISSION_DENIED_THRESHOLD": 20,
}


SECURITY_MONITORING = {
    "ENABLE_REAL_TIME_ALERTS": True,
    "ALERT_CHANNELS": ["email", "slack", "webhook"],
    "CRITICAL_EVENTS": [
        "multiple_failed_logins",
        "privilege_escalation_attempt",
        "large_data_export",
        "production_db_access_in_test",
        "sensitive_field_mass_access",
    ],
    "MONITORING_INTERVALS": {
        "FAILED_LOGIN_CHECK": 60,
        "EXPORT_PATTERN_ANALYSIS": 300,
        "SECURITY_LOG_ANALYSIS": 600,
    },
}


SECURITY_PERFORMANCE_MONITORING = {
    "TRACK_EXPORT_PERFORMANCE": True,
    "TRACK_DATABASE_QUERY_PATTERNS": True,
    "SLOW_EXPORT_THRESHOLD_SECONDS": 60,
    "SUSPICIOUS_QUERY_PATTERNS": [
        "excessive_joins",
        "full_table_scans",
        "unauthorized_table_access",
    ],
}


SECURITY_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "security_json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "extra": %(extra)s}',
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
        "security_detailed": {
            "format": "[SECURITY] %(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "security_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/kolct/security.log",
            "maxBytes": 50 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "security_json",
        },
        "audit_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/kolct/audit.log",
            "maxBytes": 100 * 1024 * 1024,
            "backupCount": 20,
            "formatter": "security_json",
        },
        "security_console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "security_detailed",
        },
    },
    "loggers": {
        "security": {
            "handlers": ["security_file", "security_console"],
            "level": "INFO",
            "propagate": False,
        },
        "security.database": {
            "handlers": ["security_file", "audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "security.exports": {
            "handlers": ["security_file", "audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "security.testing": {
            "handlers": ["security_file"],
            "level": "INFO",
            "propagate": False,
        },
        "security.errors": {
            "handlers": ["security_file", "audit_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "security.audit": {
            "handlers": ["audit_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


if ENVIRONMENT == "development":
    DATABASE_SECURITY_OPTIONS["sslmode"] = "prefer"
    EXPORT_SIZE_LIMITS = {
        role: limit * 10 for role, limit in EXPORT_SIZE_LIMITS.items()
    }
    SECURITY_ALERT_THRESHOLDS = {
        key: value * 2 for key, value in SECURITY_ALERT_THRESHOLDS.items()
    }


if (
    ENVIRONMENT == "testing"
    or os.environ.get("TESTING") == "true"
    or "pytest" in os.environ.get("_", "")
):
    TEST_DB_ENCRYPTION_ENABLED = False
    EXPORT_AUDIT_SETTINGS["LOG_ALL_EXPORTS"] = False
    SECURITY_MONITORING["ENABLE_REAL_TIME_ALERTS"] = False
