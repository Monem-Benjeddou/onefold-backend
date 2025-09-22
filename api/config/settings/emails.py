from django.core.mail.backends.smtp import EmailBackend
from decouple import config
import os

try:
    ANYMAIL = {
        "MAILGUN_API_KEY": config("MAILGUN_API_KEY"),
        "MAILGUN_SENDER_DOMAIN": config("MAILGUN_SENDER_DOMAIN"),
    }
except:
    pass


EMAIL_HOST_USER = os.environ.get("EMAIL_NO_REPLY_HOST", "no-reply@neoevents.com")
EMAIL_HOST = os.environ.get("EMAIL_OUTGOING_SERVER", "mail.neoevents.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_NO_REPLY_PASSWORD")
EMAIL_ACTIVATION_HOST = os.environ.get(
    "EMAIL_ACTIVATION_HOST", "your_account_activation@neoevents.com"
)
EMAIL_ACTIVATION_PASSWORD = os.environ.get("EMAIL_ACTIVATION_PASSWORD")


EMAIL_ACTIVATION_BACKEND = EmailBackend(
    host="mail.neoevents.com",
    port=465,
    username=EMAIL_ACTIVATION_HOST,
    password=EMAIL_ACTIVATION_PASSWORD,
    use_tls=False,
    use_ssl=True,
)


EMAIL_NO_REPLY_BACKEND = EmailBackend(
    host="mail.neoevents.com",
    port=465,
    username=EMAIL_HOST_USER,
    password=EMAIL_HOST_PASSWORD,
    use_tls=False,
    use_ssl=True,
)
