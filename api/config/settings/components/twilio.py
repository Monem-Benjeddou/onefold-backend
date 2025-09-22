"""
Twilio configuration for SMS services only.
NOTE: Email continues to use existing SendGrid configuration.
"""

from ..config_loader import get_secure_value, get_env_bool, get_config_value


TWILIO_ACCOUNT_SID = get_secure_value("TWILIO_ACCOUNT_SID", required=False)
TWILIO_AUTH_TOKEN = get_secure_value("TWILIO_AUTH_TOKEN", required=False)
TWILIO_API_KEY = get_secure_value("TWILIO_API_KEY", required=False)
TWILIO_VERIFY_SERVICE_SID = get_secure_value(
    "TWILIO_VERIFY_SERVICE_SID", required=False
)


TWILIO_SMS_FROM_NUMBER = get_secure_value("TWILIO_SMS_FROM_NUMBER", required=False)


TWILIO_SMS_ENABLED = get_env_bool("TWILIO_SMS_ENABLED", False)
TWILIO_SMS_FALLBACK_ENABLED = get_env_bool("TWILIO_SMS_FALLBACK_ENABLED", False)

# NOTE: SendGrid email configuration remains in existing email settings


TWILIO_REQUEST_TIMEOUT = get_config_value("twilio.request_timeout", 30)
TWILIO_MAX_RETRIES = get_config_value("twilio.max_retries", 3)
TWILIO_RETRY_DELAY = get_config_value("twilio.retry_delay", 1.0)


SMS_ROUTING_CONFIG = {
    "saudi_arabia": {
        "country_codes": ["966", "+966"],
        "service": "neons",
        "enabled": True,
    },
    "international": {
        "service": "twilio",
        "enabled": TWILIO_SMS_ENABLED,
        "fallback_service": "neons" if TWILIO_SMS_FALLBACK_ENABLED else None,
    },
}
