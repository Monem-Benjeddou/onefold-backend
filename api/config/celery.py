import os
from celery import Celery


DEV = os.environ.get("ENV", "False") == "1"
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "api.config.settings.production" if not DEV else "api.config.settings.development",
)

app = Celery("noev")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()