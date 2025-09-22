"""
Deployment Health Check Middleware

This middleware ensures that health check endpoints work properly during
automated deployments by bypassing SSL redirects and providing fast responses.
"""

import logging
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import time

logger = logging.getLogger(__name__)


class DeploymentHealthMiddleware(MiddlewareMixin):
    """
    Middleware specifically designed for deployment health checks.

    This middleware intercepts health check requests early in the request
    processing pipeline and returns responses directly, bypassing all
    other middleware that might cause redirects or delays.
    """

    DEPLOYMENT_HEALTH_PATHS = {
        "/deploy-health/": "deployment",
        "/deploy-status/": "deployment",
        "/ok/": "simple",
        "/health/": "comprehensive",
        "/health/basic/": "basic",
        "/health/simple/": "simple",
        "/status/": "basic",
    }

    def process_request(self, request):
        """
        Process incoming requests and handle health checks immediately.

        Args:
            request: The HTTP request object

        Returns:
            JsonResponse for health checks, None for other requests
        """
        path = request.path

        if path not in self.DEPLOYMENT_HEALTH_PATHS:
            return None

        check_type = self.DEPLOYMENT_HEALTH_PATHS[path]

        try:
            if check_type == "deployment":
                return self._deployment_health_response()
            elif check_type == "basic" or check_type == "simple":
                return self._basic_health_response()
            elif check_type == "comprehensive":
                return self._comprehensive_health_response(request)
            else:
                return self._basic_health_response()

        except Exception as e:
            logger.error(f"Health check middleware error: {e}")
            return JsonResponse(
                {
                    "status": "error",
                    "timestamp": time.time(),
                    "message": f"Health check middleware error: {str(e)}",
                },
                status=500,
            )

    def _deployment_health_response(self):
        """
        Return a deployment-specific health response.

        Returns:
            JsonResponse: Deployment health status
        """
        return JsonResponse(
            {
                "status": "ok",
                "timestamp": int(time.time()),
                "message": "deployment-ready",
                "service": "kolct-api",
            },
            status=200,
        )

    def _basic_health_response(self):
        """
        Return a basic health response for deployment monitoring.

        Returns:
            JsonResponse: Basic health status
        """
        return JsonResponse(
            {
                "status": "healthy",
                "timestamp": time.time(),
                "message": "Service is running",
                "version": getattr(settings, "VERSION", "1.0.0"),
                "check_type": "deployment",
            },
            status=200,
        )

    def _comprehensive_health_response(self, request):
        """
        Return a comprehensive health response with component checks.

        Args:
            request: The HTTP request object

        Returns:
            JsonResponse: Comprehensive health status
        """
        start_time = time.time()
        health_status = {
            "status": "healthy",
            "timestamp": start_time,
            "version": getattr(settings, "VERSION", "1.0.0"),
            "check_type": "deployment",
            "checks": {},
        }

        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status["checks"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        try:
            from django.core.cache import cache

            cache_key = "deployment_health_check"
            cache.set(cache_key, "ok", 10)
            if cache.get(cache_key) == "ok":
                health_status["checks"]["cache"] = {"status": "healthy"}
                cache.delete(cache_key)
            else:
                health_status["checks"]["cache"] = {"status": "degraded"}
        except Exception as e:

            health_status["checks"]["cache"] = {"status": "degraded", "error": str(e)}

        response_time = time.time() - start_time
        health_status["response_time_ms"] = round(response_time * 1000, 2)

        status_code = 200 if health_status["status"] == "healthy" else 503

        return JsonResponse(health_status, status=status_code)


class SSLBypassForHealthMiddleware(MiddlewareMixin):
    """
    Simpler middleware to prevent SSL redirects for health endpoints.

    This middleware runs early and marks health check requests to bypass
    SSL redirects in Django's SecurityMiddleware.
    """

    HEALTH_PATHS = [
        "/deploy-health/",
        "/deploy-status/",
        "/ok/",
        "/health/",
        "/health/basic/",
        "/health/simple/",
        "/health/ready/",
        "/health/live/",
        "/status/",
    ]

    def process_request(self, request):
        """
        Mark health check requests to bypass SSL redirects.

        Args:
            request: The HTTP request object
        """
        if request.path in self.HEALTH_PATHS:

            request.META["HTTP_X_FORWARDED_PROTO"] = "https"
            request._bypass_ssl_check = True

        return None
