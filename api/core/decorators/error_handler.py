from functools import wraps
import logging
import traceback
import re
from django_redis.exceptions import ConnectionInterrupted
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    AuthenticationFailed,
    UnsupportedMediaType,
    Throttled,
)
from django.db.utils import IntegrityError, DatabaseError, OperationalError


logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security.errors")


def flatten_validation_error(error_detail):
    """
    Flatten non_field_errors to a simple string while keeping other field errors as they are.
    """
    if isinstance(error_detail, dict):

        if len(error_detail) == 1 and "non_field_errors" in error_detail:
            non_field_errors = error_detail["non_field_errors"]
            if isinstance(non_field_errors, list) and len(non_field_errors) > 0:
                return str(non_field_errors[0])

        elif "non_field_errors" in error_detail:
            flattened = error_detail.copy()
            non_field_errors = flattened["non_field_errors"]
            if isinstance(non_field_errors, list) and len(non_field_errors) > 0:

                del flattened["non_field_errors"]

                if flattened:
                    flattened["error"] = str(non_field_errors[0])
                    return flattened
                else:

                    return str(non_field_errors[0])

    return error_detail


def sanitize_database_error(error_message: str, user=None) -> str:
    """
    Sanitize database error messages to prevent information disclosure.

    Args:
        error_message: Original error message
        user: User who encountered the error

    Returns:
        Sanitized error message
    """

    sensitive_patterns = [
        r'password[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r'user[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r'username[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r'host[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r'hostname[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r'server[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r"port[=:]\s*\d+",
        r'database[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r'dbname[=:]\s*[\'"]?[^\s\'"]*[\'"]?',
        r"DETAIL:\s*.*",
        r"HINT:\s*.*",
        r"CONTEXT:\s*.*",
        r"connection string.*",
        r"server.*host.*",
        r"secret[=:]\s*['\"]?[^\s'\"]*['\"]?",
        r"token[=:]\s*['\"]?[^\s'\"]*['\"]?",
        r"key[=:]\s*['\"]?[^\s'\"]*['\"]?",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        r"\/[a-zA-Z0-9_\-\/]+\.(?:pem|key|crt)",
    ]

    if user and not (
        getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
    ):
        security_logger.warning(
            "DATABASE_ERROR_SANITIZED_FOR_USER",
            extra={
                "user_id": getattr(user, "id", None),
                "error_type": "database_error",
                "timestamp": timezone.now().isoformat(),
            },
        )
        return (
            "A database error occurred. Please contact support if the problem persists."
        )

    sanitized_message = error_message
    for pattern in sensitive_patterns:
        sanitized_message = re.sub(
            pattern, "[REDACTED]", sanitized_message, flags=re.IGNORECASE
        )

    return sanitized_message


def api_error_handler(view_func):
    """
    Enhanced decorator for handling exceptions in API views with security focus.

    Security Features:
    - Database error sanitization
    - Audit logging of security-sensitive errors
    - Rate limiting integration
    - Information disclosure prevention
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = getattr(request, "user", None) if hasattr(request, "user") else None
        view_name = getattr(view_func, "__name__", "unknown_view")

        try:
            return view_func(request, *args, **kwargs)

        except ValidationError as e:

            security_logger.info(
                "VALIDATION_ERROR",
                extra={
                    "user_id": (
                        getattr(user, "id", None)
                        if user and user.is_authenticated
                        else None
                    ),
                    "view_name": view_name,
                    "error_detail": str(e.detail),
                    "timestamp": timezone.now().isoformat(),
                },
            )
            flattened_error = flatten_validation_error(e.detail)
            return Response(
                {"error": flattened_error}, status=status.HTTP_400_BAD_REQUEST
            )

        except PermissionDenied as e:

            security_logger.warning(
                "PERMISSION_DENIED",
                extra={
                    "user_id": (
                        getattr(user, "id", None)
                        if user and user.is_authenticated
                        else None
                    ),
                    "view_name": view_name,
                    "error": str(e),
                    "ip_address": (
                        request.META.get("REMOTE_ADDR")
                        if hasattr(request, "META")
                        else None
                    ),
                    "user_agent": (
                        request.META.get("HTTP_USER_AGENT")
                        if hasattr(request, "META")
                        else None
                    ),
                    "timestamp": timezone.now().isoformat(),
                },
            )
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except MethodNotAllowed as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        except NotAcceptable as e:
            return Response({"error": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

        except NotAuthenticated as e:

            security_logger.warning(
                "AUTHENTICATION_REQUIRED",
                extra={
                    "view_name": view_name,
                    "ip_address": (
                        request.META.get("REMOTE_ADDR")
                        if hasattr(request, "META")
                        else None
                    ),
                    "user_agent": (
                        request.META.get("HTTP_USER_AGENT")
                        if hasattr(request, "META")
                        else None
                    ),
                    "timestamp": timezone.now().isoformat(),
                },
            )
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except AuthenticationFailed as e:

            security_logger.warning(
                "AUTHENTICATION_FAILED",
                extra={
                    "view_name": view_name,
                    "error": str(e),
                    "ip_address": (
                        request.META.get("REMOTE_ADDR")
                        if hasattr(request, "META")
                        else None
                    ),
                    "user_agent": (
                        request.META.get("HTTP_USER_AGENT")
                        if hasattr(request, "META")
                        else None
                    ),
                    "timestamp": timezone.now().isoformat(),
                },
            )
            status_code = getattr(e, "status_code", None) or getattr(
                e, "code", status.HTTP_401_UNAUTHORIZED
            )
            return Response({"error": str(e)}, status=status_code)

        except UnsupportedMediaType as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        except Throttled as e:

            security_logger.warning(
                "RATE_LIMIT_EXCEEDED",
                extra={
                    "user_id": (
                        getattr(user, "id", None)
                        if user and user.is_authenticated
                        else None
                    ),
                    "view_name": view_name,
                    "ip_address": (
                        request.META.get("REMOTE_ADDR")
                        if hasattr(request, "META")
                        else None
                    ),
                    "timestamp": timezone.now().isoformat(),
                },
            )
            return Response({"error": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        except AssertionError as e:
            logger.error(f"Assertion error in {view_name}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except APIException as e:
            if hasattr(e, "detail"):
                flattened_error = flatten_validation_error(e.detail)
                return Response({"error": flattened_error}, status=e.status_code)
            return Response({"error": str(e)}, status=e.status_code)

        except ConnectionInterrupted as e:

            security_logger.error(
                "REDIS_CONNECTION_INTERRUPTED",
                extra={
                    "user_id": (
                        getattr(user, "id", None)
                        if user and user.is_authenticated
                        else None
                    ),
                    "view_name": view_name,
                    "timestamp": timezone.now().isoformat(),
                },
            )
            return Response(
                {"error": _("Service temporarily unavailable")},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except (DatabaseError, OperationalError) as e:

            original_error = str(e)
            sanitized_error = sanitize_database_error(original_error, user)

            security_logger.error(
                "DATABASE_ERROR",
                extra={
                    "user_id": (
                        getattr(user, "id", None)
                        if user and user.is_authenticated
                        else None
                    ),
                    "view_name": view_name,
                    "original_error": original_error,
                    "sanitized_error": sanitized_error,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            return Response(
                {"error": sanitized_error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except IntegrityError as e:
            error_message = str(e)

            if (
                "_user_user_phone_number_key" in error_message
                or "UNIQUE constraint failed: _user_user.phone_number" in error_message
            ):
                return Response(
                    {
                        "error": {
                            "phone_number": [
                                _("User with this phone number already exists.")
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sanitized_error = sanitize_database_error(error_message, user)

            security_logger.error(
                "DATABASE_INTEGRITY_ERROR",
                extra={
                    "user_id": (
                        getattr(user, "id", None)
                        if user and user.is_authenticated
                        else None
                    ),
                    "view_name": view_name,
                    "original_error": error_message,
                    "sanitized_error": sanitized_error,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            return Response(
                {"error": sanitized_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:

            error_traceback = traceback.format_exc()

            security_logger.error(
                "UNEXPECTED_ERROR",
                extra={
                    "user_id": (
                        getattr(user, "id", None)
                        if user and user.is_authenticated
                        else None
                    ),
                    "view_name": view_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": error_traceback,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            logger.error(f"Unexpected error in {view_name}: {error_traceback}")

            return Response(
                {"error": _("Internal Server Error")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return _wrapped_view
