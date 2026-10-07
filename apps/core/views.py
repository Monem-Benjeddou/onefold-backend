from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def health(request):
    """Liveness and dependency check: 200 when the database (and Redis, if used) respond."""
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    if settings.REDIS_URL:
        try:
            cache.set("health", "ok", 5)
            checks["cache"] = "ok" if cache.get("health") == "ok" else "unavailable"
        except Exception:
            checks["cache"] = "unavailable"
    healthy = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status=200 if healthy else 503,
    )


def index(request):
    """Root of the API: where to go next."""
    return JsonResponse(
        {
            "name": "Onefold API",
            "version": settings.SPECTACULAR_SETTINGS["VERSION"],
            "docs": request.build_absolute_uri("/api/docs/"),
            "schema": request.build_absolute_uri("/api/schema/"),
            "health": request.build_absolute_uri("/health/"),
        }
    )
