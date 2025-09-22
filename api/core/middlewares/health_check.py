"""
Health check middleware to bypass SSL redirects for health endpoints.

This middleware allows health check endpoints to work with HTTP requests
even when SECURE_SSL_REDIRECT is enabled in production.
"""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class HealthCheckSSLBypassMiddleware(MiddlewareMixin):
    """
    Middleware to bypass SSL redirects for health check endpoints.

    This allows deployment health checks to use HTTP without getting
    301 redirects to HTTPS, which can cause health check failures.
    """

    HEALTH_CHECK_PATHS = [
        "/health/",
        "/health/basic/",
        "/health/simple/",
        "/health/ready/",
        "/health/live/",
        "/status/",
    ]

    def process_request(self, request):
        """
        Process the request and bypass SSL redirects for health endpoints.

        Args:
            request: The HTTP request object

        Returns:
            None to continue processing, or an HttpResponse to bypass
        """

        if request.path in self.HEALTH_CHECK_PATHS:

            request._bypass_ssl_redirect = True

            if not request.is_secure() and getattr(
                settings, "SECURE_SSL_REDIRECT", False
            ):
                from django.urls import resolve

                try:

                    resolved = resolve(request.path)
                    return resolved.func(request)
                except Exception:

                    pass

        return None

    def process_response(self, request, response):
        """
        Process the response and bypass SSL redirects for health endpoints.

        Args:
            request: The HTTP request object
            response: The HTTP response object

        Returns:
            The original response or a modified response
        """

        if not getattr(settings, "SECURE_SSL_REDIRECT", False):
            return response

        if (
            hasattr(request, "_bypass_ssl_redirect")
            and request._bypass_ssl_redirect
            and request.path in self.HEALTH_CHECK_PATHS
        ):

            if (
                isinstance(response, HttpResponsePermanentRedirect)
                and response.url
                and response.url.startswith("https://")
            ):

                from django.urls import resolve

                try:
                    resolved = resolve(request.path)
                    return resolved.func(request)
                except Exception:

                    pass

        return response
