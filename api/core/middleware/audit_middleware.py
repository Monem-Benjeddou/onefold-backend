"""
Comprehensive audit logging middleware for API operations.

This middleware provides automatic audit logging for all API requests with:
- User activity tracking
- Security event detection
- Performance monitoring
- Compliance logging
"""

import json
import uuid
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger("security.audit")


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive API audit logging.

    Logs all authenticated API requests with security context.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.sensitive_paths = getattr(
            settings,
            "AUDIT_SENSITIVE_PATHS",
            [
                "/api/auth/login/",
                "/api/auth/logout/",
                "/api/payment/",
                "/api/cards/private-keys/",
                "/api/admin/",
            ],
        )
        self.excluded_paths = getattr(
            settings,
            "AUDIT_EXCLUDED_PATHS",
            ["/api/health/", "/api/docs/", "/static/", "/media/"],
        )
        self.log_anonymous = getattr(settings, "AUDIT_LOG_ANONYMOUS", False)
        self.log_response_body = getattr(settings, "AUDIT_LOG_RESPONSE_BODY", False)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request for audit logging.

        Args:
            request: The incoming HTTP request
        """

        if self._should_skip_path(request.path):
            return None

        request.audit_id = str(uuid.uuid4())
        request.audit_start_time = time.time()

        request.audit_context = {
            "request_id": request.audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.path,
            "ip_address": self._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "is_sensitive": self._is_sensitive_path(request.path),
        }

        if hasattr(request, "user") and not isinstance(request.user, AnonymousUser):
            request.audit_context["user"] = {
                "id": request.user.id,
                "username": getattr(request.user, "username", ""),
                "email": getattr(request.user, "email", ""),
                "role": getattr(request.user, "role", "user"),
                "is_staff": getattr(request.user, "is_staff", False),
            }
        elif self.log_anonymous:
            request.audit_context["user"] = {"anonymous": True}

        if request.audit_context.get("is_sensitive"):
            self._log_sensitive_request(request)

        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """
        Process response for audit logging.

        Args:
            request: The HTTP request
            response: The HTTP response

        Returns:
            The HTTP response
        """

        if not hasattr(request, "audit_context"):
            return response

        duration = time.time() - request.audit_start_time

        request.audit_context.update(
            {
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_size": (
                    len(response.content) if hasattr(response, "content") else 0
                ),
            }
        )

        self._detect_security_events(request, response)

        self._create_audit_log(request, response)

        if "user" in request.audit_context and request.audit_context["user"].get("id"):
            self._track_user_activity(request.audit_context["user"]["id"], request)

        return response

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> Optional[HttpResponse]:
        """
        Process exceptions for audit logging.

        Args:
            request: The HTTP request
            exception: The exception that occurred
        """
        if hasattr(request, "audit_context"):
            request.audit_context["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)[:500],
            }

            if self._is_security_exception(exception):
                logger.error(
                    f"Security exception in request {request.audit_id}: {type(exception).__name__}",
                    extra={"audit_context": request.audit_context},
                )

        return None

    def _should_skip_path(self, path: str) -> bool:
        """Check if path should be excluded from audit logging."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    def _is_sensitive_path(self, path: str) -> bool:
        """Check if path contains sensitive operations."""
        return any(path.startswith(sensitive) for sensitive in self.sensitive_paths)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    def _log_sensitive_request(self, request: HttpRequest):
        """Log details for sensitive requests."""

        safe_body = self._sanitize_request_body(request)

        logger.info(
            f"Sensitive operation: {request.method} {request.path}",
            extra={
                "audit_id": request.audit_id,
                "user": request.audit_context.get("user", {}),
                "body_sample": safe_body[:200] if safe_body else None,
            },
        )

    def _sanitize_request_body(self, request: HttpRequest) -> Optional[str]:
        """Sanitize request body to remove sensitive data."""
        try:
            if request.body:
                body_str = request.body.decode("utf-8")

                try:
                    body_json = json.loads(body_str)

                    sensitive_fields = [
                        "password",
                        "token",
                        "secret",
                        "private_key",
                        "api_key",
                    ]
                    for field in sensitive_fields:
                        if field in body_json:
                            body_json[field] = "[REDACTED]"
                    return json.dumps(body_json)
                except json.JSONDecodeError:

                    return body_str[:200]
        except Exception:
            return None

    def _detect_security_events(self, request: HttpRequest, response: HttpResponse):
        """Detect and log security-relevant events."""
        events = []

        if request.path.startswith("/api/auth/") and response.status_code == 401:
            events.append("authentication_failed")
            self._track_failed_auth(request)

        if response.status_code == 403:
            events.append("authorization_denied")

        if response.status_code == 429:
            events.append("rate_limit_exceeded")

        if self._detect_suspicious_patterns(request):
            events.append("suspicious_activity")

        if events:
            request.audit_context["security_events"] = events
            logger.warning(
                f"Security events detected: {', '.join(events)}",
                extra={"audit_context": request.audit_context},
            )

    def _detect_suspicious_patterns(self, request: HttpRequest) -> bool:
        """Detect suspicious request patterns."""
        suspicious_indicators = []

        if request.GET:
            query_string = request.GET.urlencode().lower()
            sql_patterns = [
                "select ",
                "union ",
                "drop ",
                "insert ",
                "update ",
                "delete ",
            ]
            if any(pattern in query_string for pattern in sql_patterns):
                suspicious_indicators.append("sql_injection_attempt")

        if "../" in request.path or "..\\" in request.path:
            suspicious_indicators.append("path_traversal_attempt")

        if hasattr(request, "audit_context"):
            ip = request.audit_context.get("ip_address")
            if ip:
                rate_key = f"request_rate:{ip}"
                request_count = cache.get(rate_key, 0)
                if request_count > 100:
                    suspicious_indicators.append("excessive_request_rate")

        return len(suspicious_indicators) > 0

    def _is_security_exception(self, exception: Exception) -> bool:
        """Check if exception is security-related."""
        security_exceptions = [
            "PermissionDenied",
            "AuthenticationFailed",
            "NotAuthenticated",
            "InvalidToken",
            "TokenError",
        ]
        return type(exception).__name__ in security_exceptions

    def _create_audit_log(self, request: HttpRequest, response: HttpResponse):
        """Create audit log entry."""

        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING

        logger.log(
            log_level,
            f"{request.method} {request.path} - {response.status_code} ({request.audit_context.get('duration_ms', 0)}ms)",
            extra={"audit_context": request.audit_context},
        )

        try:
            from core.models import AuditLog

            AuditLog.objects.create(
                request_id=request.audit_id,
                user_id=request.audit_context.get("user", {}).get("id"),
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration_ms=request.audit_context.get("duration_ms", 0),
                ip_address=request.audit_context.get("ip_address"),
                user_agent=request.audit_context.get("user_agent"),
                security_events=request.audit_context.get("security_events", []),
                metadata=request.audit_context,
            )
        except ImportError:
            pass

    def _track_user_activity(self, user_id: int, request: HttpRequest):
        """Track user activity patterns."""

        cache_key = f"user_activity:{user_id}"
        activity = cache.get(
            cache_key, {"last_seen": None, "request_count": 0, "paths": []}
        )

        activity["last_seen"] = datetime.now(timezone.utc).isoformat()
        activity["request_count"] += 1

        if request.path not in activity["paths"]:
            activity["paths"].append(request.path)
            activity["paths"] = activity["paths"][-10:]

        cache.set(cache_key, activity, timeout=3600)

    def _track_failed_auth(self, request: HttpRequest):
        """Track failed authentication attempts."""
        ip = request.audit_context.get("ip_address")
        if ip:
            cache_key = f"failed_auth:{ip}"
            attempts = cache.get(cache_key, 0)
            attempts += 1
            cache.set(cache_key, attempts, timeout=300)

            if attempts >= 5:
                logger.critical(
                    f"Multiple failed authentication attempts from {ip}",
                    extra={"ip_address": ip, "attempts": attempts},
                )
