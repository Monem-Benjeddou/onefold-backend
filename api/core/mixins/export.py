"""
ExportMixin for Django REST Framework views.

Provides standardized export functionality with CSV and JSON support,
security features, and performance optimizations for large datasets.
"""

import csv
import json
import re
import uuid
import hashlib
from datetime import datetime
from io import StringIO
from typing import Dict, List, Optional, Any, Union

from django.db.models import QuerySet
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import logging

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit


try:
    from core.security.export_security import (
        access_controller,
        data_sanitizer,
        audit_logger_instance,
        ExportSecurityLevel,
        secure_export_operation,
    )

    EXPORT_SECURITY_AVAILABLE = True
except ImportError:
    EXPORT_SECURITY_AVAILABLE = False
    access_controller = None
    data_sanitizer = None
    audit_logger_instance = None
    ExportSecurityLevel = None
    secure_export_operation = None

audit_logger = logging.getLogger("security.exports")
export_security_logger = logging.getLogger("security.export_operations")


DEFAULT_CHUNK_SIZE = 1000
MAX_EXPORT_SIZE = 50000
CSV_DANGEROUS_CHARS = re.compile(r"^[\s]*[=+\-@|]")
FILENAME_SANITIZER = re.compile(r'[<>:"/\\|?*]')


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle Django-specific types.
    """

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def sanitize_csv_field(value: Any) -> str:
    """
    Sanitize CSV field to prevent formula injection attacks.

    Removes or escapes dangerous characters that could be interpreted as formulas:
    - Equals sign (=)
    - Plus sign (+)
    - Minus sign (-)
    - At sign (@)
    - Pipe character (|)
    - Tab characters

    Args:
        value: The field value to sanitize

    Returns:
        str: Sanitized field value
    """
    if value is None:
        return ""

    value_str = str(value)

    if (
        CSV_DANGEROUS_CHARS.match(value_str)
        or "\r" in value_str
        or "\n" in value_str
        or "\t" in value_str
    ):

        value_str = "'" + value_str

    return value_str


def sanitize_filename(filename: str, default_extension: str = "csv") -> str:
    """
    Sanitize filename to prevent path injection and ensure safe naming.

    Args:
        filename: The filename to sanitize
        default_extension: Default file extension if none provided

    Returns:
        str: Sanitized filename
    """

    sanitized = filename

    sanitized = sanitized.replace("../", "_.._")
    sanitized = sanitized.replace("..\\", "_.._")

    sanitized = sanitized.replace("/", "_")
    sanitized = sanitized.replace("\\", "_")
    for char in '<>:"|?*':
        sanitized = sanitized.replace(char, "_")

    sanitized = sanitized.replace("..", "_")

    if "." not in sanitized or sanitized.count(".") == sanitized.count("_"):
        sanitized = f"{sanitized}.{default_extension}"
    elif not sanitized.endswith(f".{default_extension}"):

        base_parts = sanitized.split(".")
        if len(base_parts) > 1:
            base_name = base_parts[0]
            sanitized = f"{base_name}.{default_extension}"
        else:
            sanitized = f"{sanitized}.{default_extension}"

    return sanitized


class ExportMixin:
    """
    Mixin to add export functionality to DRF ViewSets and API views.

    Supports CSV and JSON export with filtering, field selection,
    streaming for large datasets, and comprehensive security measures.

    Usage:
        class MyViewSet(ExportMixin, viewsets.ModelViewSet):
            export_fields = ['id', 'name', 'email']
            export_filename_prefix = 'users'
    """

    export_fields: List[str] = []
    export_filename_prefix: str = "export"
    export_chunk_size: int = DEFAULT_CHUNK_SIZE
    export_max_size: int = MAX_EXPORT_SIZE
    export_cache_ttl: int = 300
    export_enable_cache: bool = True

    def get_format_suffix(self, **kwargs):
        """
        Override format suffix to prevent DRF from treating 'format'
        query parameter as a format suffix that needs renderer validation.

        This allows us to handle CSV export manually without requiring
        a CSV renderer in DRF settings.
        """
        return None

    def perform_content_negotiation(self, request, force=False):
        """
        Override content negotiation to bypass format validation.

        Since we handle CSV export manually with StreamingHttpResponse,
        we don't need DRF to validate the format parameter against
        available renderers.
        """

        renderers = self.get_renderers()
        if renderers:
            renderer = renderers[0]
            media_type = renderer.media_type
            return renderer, media_type

        return super().perform_content_negotiation(request, force)

    def get_export_queryset(self) -> QuerySet:
        """
        Get the queryset for export with performance optimizations.

        By default, uses the view's filtered queryset with export-specific optimizations.
        Override this method to customize the export queryset.

        Returns:
            QuerySet: The queryset to export
        """
        if hasattr(self, "filter_queryset"):
            queryset = self.filter_queryset(self.get_queryset())
        else:
            queryset = self.get_queryset()

        return self.optimize_queryset_for_export(queryset)

    def optimize_queryset_for_export(self, queryset: QuerySet) -> QuerySet:
        """
        Apply performance optimizations for export operations.

        Args:
            queryset: Base queryset to optimize

        Returns:
            QuerySet: Optimized queryset for export
        """
        try:
            from core.utils.query_optimization import QueryOptimizer

            query_params = getattr(self.request, "query_params", self.request.GET)
            fields_param = query_params.get("fields")
            selected_fields = None
            if fields_param:
                selected_fields = [f.strip() for f in fields_param.split(",")]

            return QueryOptimizer.optimize_for_export(queryset, selected_fields)
        except (ImportError, Exception):

            return queryset

    def get_export_fields(self, format_type: str) -> List[str]:
        """
        Get the fields to include in the export.

        Args:
            format_type: The export format ('csv' or 'json')

        Returns:
            List[str]: List of field names to include
        """
        query_params = getattr(self.request, "query_params", self.request.GET)
        fields_param = query_params.get("fields")
        if fields_param:
            requested_fields = [f.strip() for f in fields_param.split(",")]

            if self.export_fields:
                valid_fields = [f for f in requested_fields if f in self.export_fields]
                if not valid_fields:

                    return self.export_fields
                return valid_fields
            else:

                serializer_class = self.get_serializer_class()
                serializer = serializer_class()
                available_fields = list(serializer.fields.keys())
                return [f for f in requested_fields if f in available_fields]

        if self.export_fields:
            return self.export_fields

        serializer_class = self.get_serializer_class()
        serializer = serializer_class()
        return list(serializer.fields.keys())

    def filter_queryset_by_ids(self, queryset: QuerySet) -> QuerySet:
        """
        Filter queryset by comma-separated IDs from query parameter.

        Args:
            queryset: The base queryset

        Returns:
            QuerySet: Filtered queryset
        """
        query_params = getattr(self.request, "query_params", self.request.GET)
        ids_param = query_params.get("ids")
        if ids_param:
            raw_ids = [
                id_str.strip() for id_str in ids_param.split(",") if id_str.strip()
            ]
            if raw_ids:

                model_field = queryset.model._meta.get_field("id")

                if hasattr(model_field, "get_internal_type"):
                    field_type = model_field.get_internal_type()

                    if field_type in ["AutoField", "BigAutoField", "IntegerField"]:

                        valid_ids = []
                        for id_str in raw_ids:
                            try:
                                valid_ids.append(int(id_str))
                            except ValueError:

                                continue

                        if valid_ids:
                            queryset = queryset.filter(id__in=valid_ids)

                    else:

                        try:
                            queryset = queryset.filter(id__in=raw_ids)
                        except Exception:

                            pass
                else:

                    try:

                        int_ids = [int(id_str) for id_str in raw_ids]
                        queryset = queryset.filter(id__in=int_ids)
                    except ValueError:
                        try:

                            queryset = queryset.filter(id__in=raw_ids)
                        except Exception:

                            pass

        return queryset

    def get_export_filename(self, format_type: str, queryset: QuerySet) -> str:
        """
        Generate filename for the export.

        Args:
            format_type: The export format ('csv' or 'json')
            queryset: The queryset being exported

        Returns:
            str: Generated filename
        """
        query_params = getattr(self.request, "query_params", self.request.GET)
        custom_filename = query_params.get("filename")
        if custom_filename:
            return sanitize_filename(custom_filename, format_type)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = queryset.model.__name__.lower()
        filename = (
            f"{self.export_filename_prefix}_{model_name}_{timestamp}.{format_type}"
        )

        return sanitize_filename(filename, format_type)

    def serialize_export_data(
        self, queryset: QuerySet, fields: List[str]
    ) -> List[Dict]:
        """
        Serialize queryset data for export.

        Args:
            queryset: The queryset to serialize
            fields: List of fields to include

        Returns:
            List[Dict]: Serialized data
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            queryset, many=True, context={"request": self.request}
        )

        if fields:
            filtered_data = []
            for item in serializer.data:
                filtered_item = {key: item.get(key) for key in fields if key in item}
                filtered_data.append(filtered_item)
            return filtered_data

        return serializer.data

    def get_export_field_value(self, obj, field_name: str):
        """
        Get field value from model instance for export.

        This method provides direct attribute access instead of full serialization
        for better performance during exports.

        Args:
            obj: Model instance
            field_name: Field name to extract

        Returns:
            Field value or empty string if not found
        """
        try:

            if "." in field_name:
                parts = field_name.split(".")
                value = obj
                for part in parts:
                    if hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        return ""
                return value

            if hasattr(obj, field_name):
                value = getattr(obj, field_name)

                if value is None:
                    return ""
                elif hasattr(value, "strftime"):
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, bool):
                    return "Yes" if value else "No"
                else:
                    return str(value)

            return ""

        except Exception:

            return ""

    def get_cache_key(
        self, format_type: str, fields: List[str], queryset_params: Dict
    ) -> str:
        """
        Generate cache key for export data.

        Args:
            format_type: Export format (csv/json)
            fields: Fields being exported
            queryset_params: Parameters affecting the queryset

        Returns:
            str: Cache key
        """

        key_parts = [
            self.__class__.__name__,
            format_type,
            ",".join(sorted(fields)),
            str(sorted(queryset_params.items())),
            (
                str(self.request.user.id)
                if self.request.user.is_authenticated
                else "anonymous"
            ),
        ]

        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"export:{self.export_filename_prefix}:{key_hash}"

    def get_cached_export_data(self, cache_key: str):
        """
        Get cached export data.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Cached data or None if not found
        """
        if not self.export_enable_cache:
            return None

        try:
            return cache.get(cache_key)
        except Exception:

            return None

    def cache_export_data(self, cache_key: str, data: Any) -> None:
        """
        Cache export data.

        Args:
            cache_key: Cache key to store under
            data: Data to cache
        """
        if not self.export_enable_cache:
            return

        try:
            cache.set(cache_key, data, self.export_cache_ttl)
        except Exception:

            pass

    def get_chunked_queryset(self, queryset: QuerySet, chunk_size: int = None):
        """
        Generator that yields queryset chunks for memory-efficient processing with
        enhanced concurrency support.

        Args:
            queryset: The queryset to chunk
            chunk_size: Size of each chunk (defaults to export_chunk_size)

        Yields:
            QuerySet chunks
        """
        from django.db import connection, transaction
        import time
        import random

        chunk_size = chunk_size or min(self.export_chunk_size, 500)

        try:

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with transaction.atomic():

                        total_count = queryset.count()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise

                    time.sleep(0.1 + random.uniform(0, 0.1))

            for offset in range(0, total_count, chunk_size):

                try:

                    chunk_queryset = queryset[offset : offset + chunk_size]
                    yield chunk_queryset
                except Exception as e:

                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error in queryset chunk at offset {offset}: {e}")

                    if hasattr(connection, "close"):
                        connection.close()
                    continue

        except Exception as e:

            if hasattr(connection, "close"):
                connection.close()
            raise

    def generate_csv_response(
        self, queryset: QuerySet, filename: str, fields: List[str]
    ) -> HttpResponse:
        """
        Generate CSV response for export with optimized memory usage and performance.

        Args:
            queryset: The queryset to export
            filename: The filename for the export
            fields: List of fields to include

        Returns:
            HttpResponse: CSV response
        """

        try:
            from core.utils.query_optimization import monitor_queries
        except ImportError:

            def monitor_queries(desc=None):
                def decorator(func):
                    return func

                return decorator

        @monitor_queries(f"CSV Export - {filename}")
        def csv_generator():
            """Generator function for streaming CSV response with memory optimization and concurrency support."""
            from django.db import transaction, connection
            import logging

            logger = logging.getLogger(__name__)
            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(fields)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            processed_count = 0
            old_autocommit = None

            try:

                old_autocommit = None
                if not getattr(connection, "in_atomic_block", False):
                    try:
                        old_autocommit = connection.get_autocommit()
                        if not old_autocommit:
                            connection.set_autocommit(True)
                    except Exception:

                        old_autocommit = None

                for chunk_queryset in self.get_chunked_queryset(queryset):

                    try:
                        with transaction.atomic():

                            for item in chunk_queryset.iterator(chunk_size=50):
                                try:
                                    row = []
                                    for field in fields:
                                        value = self.get_export_field_value(item, field)
                                        sanitized_value = sanitize_csv_field(value)
                                        row.append(sanitized_value)

                                    writer.writerow(row)
                                    processed_count += 1

                                    if len(output.getvalue()) > 4096:
                                        yield output.getvalue()
                                        output.seek(0)
                                        output.truncate(0)

                                except Exception as row_error:
                                    logger.warning(
                                        f"Error processing row {processed_count}: {row_error}"
                                    )
                                    continue

                        if output.getvalue():
                            yield output.getvalue()
                            output.seek(0)
                            output.truncate(0)

                    except Exception as chunk_error:
                        logger.warning(f"Error processing chunk: {chunk_error}")

                        connection.close()
                        continue

            except Exception as e:
                logger.error(f"CSV export error: {e}")

                if hasattr(connection, "close"):
                    connection.close()
                raise
            finally:

                if old_autocommit is not None:
                    try:
                        connection.set_autocommit(old_autocommit)
                    except Exception:
                        pass

            logger.info(
                f"CSV export completed: {processed_count} records exported to {filename}"
            )

        response = StreamingHttpResponse(csv_generator(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        response["X-Export-Type"] = "csv"
        response["X-Export-Fields"] = str(len(fields))

        return response

    def generate_json_response(
        self, queryset: QuerySet, filename: str, fields: List[str]
    ) -> HttpResponse:
        """
        Generate JSON response for export with memory optimization and performance monitoring.

        Args:
            queryset: The queryset to export
            filename: The filename for the export
            fields: List of fields to include

        Returns:
            HttpResponse: JSON response
        """

        try:
            from core.utils.query_optimization import monitor_queries
        except ImportError:

            def monitor_queries(desc=None):
                def decorator(func):
                    return func

                return decorator

        @monitor_queries(f"JSON Export - {filename}")
        def json_generator():
            """Generator function for streaming JSON response with memory optimization and concurrency support."""
            from django.db import transaction, connection
            import logging

            logger = logging.getLogger(__name__)
            yield "[\n"

            first_item = True
            processed_count = 0
            old_autocommit = None

            try:

                old_autocommit = None
                if not getattr(connection, "in_atomic_block", False):
                    try:
                        old_autocommit = connection.get_autocommit()
                        if not old_autocommit:
                            connection.set_autocommit(True)
                    except Exception:

                        old_autocommit = None

                for chunk_queryset in self.get_chunked_queryset(queryset):
                    try:
                        with transaction.atomic():
                            for item in chunk_queryset.iterator(chunk_size=50):
                                try:
                                    if not first_item:
                                        yield ",\n"

                                    item_data = {}
                                    for field in fields:
                                        item_data[field] = self.get_export_field_value(
                                            item, field
                                        )

                                    item_json = json.dumps(
                                        item_data,
                                        cls=CustomJSONEncoder,
                                        indent=2,
                                        ensure_ascii=False,
                                    )
                                    yield item_json

                                    first_item = False
                                    processed_count += 1

                                except Exception as row_error:
                                    logger.warning(
                                        f"Error processing JSON row {processed_count}: {row_error}"
                                    )
                                    continue

                    except Exception as chunk_error:
                        logger.warning(f"Error processing JSON chunk: {chunk_error}")

                        connection.close()
                        continue

            except Exception as e:
                logger.error(f"JSON export error: {e}")

                if hasattr(connection, "close"):
                    connection.close()
                raise
            finally:

                if old_autocommit is not None:
                    try:
                        connection.set_autocommit(old_autocommit)
                    except Exception:
                        pass

            yield "\n]"

            logger.info(
                f"JSON export completed: {processed_count} records exported to {filename}"
            )

        response = StreamingHttpResponse(
            json_generator(), content_type="application/json"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        response["X-Export-Type"] = "json"
        response["X-Export-Fields"] = str(len(fields))

        return response

    def log_export_attempt(
        self, format_type: str, record_count: int, fields: List[str]
    ) -> None:
        """
        Log export attempt for security auditing.

        Args:
            format_type: The export format
            record_count: Number of records being exported
            fields: List of fields being exported
        """
        audit_logger.warning(
            "DATA_EXPORT_ATTEMPT",
            extra={
                "user_id": (
                    str(self.request.user.id)
                    if self.request.user.is_authenticated
                    else None
                ),
                "username": (
                    self.request.user.username
                    if self.request.user.is_authenticated
                    else None
                ),
                "user_role": (
                    getattr(self.request.user, "role", None)
                    if self.request.user.is_authenticated
                    else None
                ),
                "export_format": format_type,
                "record_count": record_count,
                "exported_fields": fields,
                "filter_params": dict(
                    getattr(self.request, "query_params", self.request.GET)
                ),
                "ip_address": self.request.META.get("REMOTE_ADDR"),
                "user_agent": self.request.META.get("HTTP_USER_AGENT"),
                "timestamp": timezone.now().isoformat(),
                "view_class": self.__class__.__name__,
            },
        )

        if record_count > 10000:
            audit_logger.critical(
                "LARGE_DATA_EXPORT",
                extra={
                    "user_id": (
                        str(self.request.user.id)
                        if self.request.user.is_authenticated
                        else None
                    ),
                    "record_count": record_count,
                    "timestamp": timezone.now().isoformat(),
                    "view_class": self.__class__.__name__,
                },
            )

    def validate_export_request(self, queryset: QuerySet) -> Optional[Response]:
        """
        Validate export request and return error response if invalid.

        Args:
            queryset: The queryset to validate

        Returns:
            Optional[Response]: Error response if validation fails, None if valid
        """
        try:
            record_count = queryset.count()
        except Exception as e:

            return Response(
                {
                    "error": _("Invalid query parameters"),
                    "detail": _(
                        "Unable to process the export request. Please check your parameters."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if record_count == 0:
            return Response(
                {"error": _("No data available for export")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if record_count > self.export_max_size:
            return Response(
                {
                    "error": _("Export size too large"),
                    "detail": _(
                        "Maximum {max_size} records allowed, {count} requested"
                    ).format(max_size=self.export_max_size, count=record_count),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return None

    @extend_schema(
        tags=["Export"],
        summary="Export data",
        description="Export data in CSV or JSON format with optional filtering and field selection",
        parameters=[
            OpenApiParameter(
                "format",
                OpenApiTypes.STR,
                enum=["csv", "json"],
                default="csv",
                description="Export format",
            ),
            OpenApiParameter(
                "ids",
                OpenApiTypes.STR,
                description="Comma-separated list of record IDs to export",
            ),
            OpenApiParameter(
                "fields",
                OpenApiTypes.STR,
                description="Comma-separated list of fields to include in export",
            ),
            OpenApiParameter(
                "filename",
                OpenApiTypes.STR,
                description="Custom filename for the export",
            ),
        ],
        responses={
            200: {
                "description": "Data exported successfully",
                "content": {
                    "text/csv": {"schema": {"type": "string", "format": "binary"}},
                    "application/json": {
                        "schema": {"type": "string", "format": "binary"}
                    },
                },
            },
            400: {"description": "Bad Request - Invalid parameters or empty dataset"},
            403: {"description": "Permission denied"},
            429: {"description": "Rate limit exceeded"},
        },
    )
    @action(detail=False, methods=["get", "post"])
    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=300)
    def export(self, request, *args, **kwargs):
        """
        Export data in CSV or JSON format with enhanced security.

        Supports:
        - Format selection (csv/json)
        - Field selection via 'fields' parameter
        - ID-based filtering via 'ids' parameter
        - Custom filename via 'filename' parameter
        - Streaming for large datasets
        - Security auditing and access control
        """

        query_params = getattr(request, "query_params", request.GET)
        export_format = query_params.get("format", "csv").lower()
        if export_format not in ["csv", "json"]:
            return Response(
                {"error": _("Invalid format. Supported formats: csv, json")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if EXPORT_SECURITY_AVAILABLE:

            queryset = self.get_export_queryset()
            requested_fields = self.get_export_fields(export_format)

            is_allowed, reason, filtered_fields = (
                access_controller.validate_export_access(
                    request.user, queryset, requested_fields, export_type=export_format
                )
            )

            if not is_allowed:
                export_security_logger.warning(
                    "EXPORT_ACCESS_DENIED",
                    extra={
                        "user_id": (
                            request.user.id if request.user.is_authenticated else None
                        ),
                        "reason": reason,
                        "requested_fields": requested_fields,
                        "timestamp": timezone.now().isoformat(),
                    },
                )
                return Response({"error": reason}, status=status.HTTP_403_FORBIDDEN)

            session_id = audit_logger_instance.start_export_session(
                request.user, export_format, queryset, filtered_fields
            )

        queryset = self.get_export_queryset()

        if EXPORT_SECURITY_AVAILABLE:

            queryset = access_controller._apply_ownership_filter(request.user, queryset)

        queryset = self.filter_queryset_by_ids(queryset)

        validation_error = self.validate_export_request(queryset)
        if validation_error:
            if EXPORT_SECURITY_AVAILABLE:
                audit_logger_instance.end_export_session(
                    session_id, success=False, error="Validation failed"
                )
            return validation_error

        fields = self.get_export_fields(export_format)
        if EXPORT_SECURITY_AVAILABLE and filtered_fields:

            fields = [f for f in fields if f in filtered_fields]

        if not fields:
            if EXPORT_SECURITY_AVAILABLE:
                audit_logger_instance.end_export_session(
                    session_id, success=False, error="No valid fields"
                )
            return Response(
                {"error": _("No valid fields specified for export")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record_count = queryset.count()
        self.log_export_attempt(export_format, record_count, fields)

        export_security_logger.info(
            "SECURE_EXPORT_INITIATED",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "user_role": getattr(request.user, "role", "unknown"),
                "export_format": export_format,
                "record_count": record_count,
                "field_count": len(fields),
                "fields": fields,
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "timestamp": timezone.now().isoformat(),
            },
        )

        filename = self.get_export_filename(export_format, queryset)

        try:

            if export_format == "json":
                response = self.generate_json_response(queryset, filename, fields)
            else:
                response = self.generate_csv_response(queryset, filename, fields)

            if EXPORT_SECURITY_AVAILABLE:
                audit_logger_instance.end_export_session(
                    session_id, success=True, exported_count=record_count
                )

            return response

        except Exception as e:

            if EXPORT_SECURITY_AVAILABLE:
                audit_logger_instance.end_export_session(
                    session_id, success=False, error=str(e)
                )
            raise


class ModelExportMixin(ExportMixin):
    """
    Specialized export mixin for Django models with common configurations.

    Provides sensible defaults for model-based exports.
    """

    def get_export_filename_prefix(self):
        """Get filename prefix based on model name."""
        if hasattr(self, "queryset") and self.queryset is not None:
            return self.queryset.model.__name__.lower()
        elif hasattr(self, "model") and self.model is not None:
            return self.model.__name__.lower()
        return self.export_filename_prefix

    def get_export_filename(self, format_type: str, queryset: QuerySet) -> str:
        """Generate filename using model name."""
        query_params = getattr(self.request, "query_params", self.request.GET)
        custom_filename = query_params.get("filename")
        if custom_filename:
            return sanitize_filename(custom_filename, format_type)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = self.get_export_filename_prefix()
        filename = f"{prefix}_export_{timestamp}.{format_type}"

        return sanitize_filename(filename, format_type)
