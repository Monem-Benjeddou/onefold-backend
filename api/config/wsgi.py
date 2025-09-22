import os
from django.core.wsgi import get_wsgi_application

DEV = os.environ.get("ENV", "False") == "1"

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "api.config.settings.production" if not DEV else "api.config.settings.development",
)

application = get_wsgi_application()
