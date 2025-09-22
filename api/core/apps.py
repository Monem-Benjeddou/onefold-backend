from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    label = "core"

    def ready(self):
        """
        Import signals and apply patches when Django starts up.
        """
        try:
            from .signals import cache_signals
        except ImportError:
            pass
