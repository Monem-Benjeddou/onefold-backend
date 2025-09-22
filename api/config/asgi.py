import os
import django
from django.core.asgi import get_asgi_application


DEV = os.environ.get("ENV", "False") == "1"

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.production" if not DEV else "config.settings.development",
)


django.setup()


from channels.routing import ProtocolTypeRouter, URLRouter
from apps.notifications.routing import websocket_urlpatterns as notification_patterns
from core.middlewares.channels import JWTAuthMiddlewareStack


all_websocket_patterns = notification_patterns


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JWTAuthMiddlewareStack(URLRouter(all_websocket_patterns)),
    }
)
