from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils.translation import gettext_lazy as _
import csv
import json
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.functional import Promise
from django.utils.encoding import force_str

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from core.mixins.export import sanitize_csv_field
from apps.accounts.user.models import User
from apps.accounts.user.serializers import UserExportSerializer
from core.abstract.permissions import ExportPermission
import logging


audit_logger = logging.getLogger("security.exports")


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


@extend_schema(tags=["Export"])
class ExportUsersView(APIView):
    """
    View for exporting users data as CSV or JSON.
    """

    permission_classes = [IsAuthenticated, ExportPermission]

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

        Since we handle CSV export manually with HttpResponse,
        we don't need DRF to validate the format parameter against
        available renderers.
        """

        renderers = self.get_renderers()
        if renderers:
            renderer = renderers[0]
            media_type = renderer.media_type
            return renderer, media_type

        return super().perform_content_negotiation(request, force)

    def get_queryset(self):
        """
        Get the filtered queryset of users to export.
        """
        queryset = User.objects.all()

        include_superusers = (
            self.request.query_params.get("include_superusers", "").lower() == "true"
        )
        if not include_superusers:
            queryset = queryset.exclude(is_superuser=True)

        role = self.request.query_params.get("role")
        if role:

            if "," in role:
                roles = role.split(",")
                queryset = queryset.filter(role__in=roles)
            else:

                roles = self.request.query_params.getlist("role")
                if len(roles) > 1:
                    queryset = queryset.filter(role__in=roles)
                else:
                    queryset = queryset.filter(role=role)

        email = self.request.query_params.get("email")
        if email:
            queryset = queryset.filter(email__icontains=email)

        email_exact = self.request.query_params.get("email_exact")
        if email_exact:
            queryset = queryset.filter(email=email_exact)

        email_domain = self.request.query_params.get("email_domain")
        if email_domain:
            queryset = queryset.filter(email__iendswith=f"@{email_domain}")

        username = self.request.query_params.get("username")
        if username:
            queryset = queryset.filter(username__icontains=username)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            is_active_bool = is_active.lower() == "true"

            if is_active_bool:

                thirty_days_ago = timezone.now() - timedelta(days=30)
                queryset = queryset.filter(
                    Q(last_login__gte=thirty_days_ago) | Q(created__gte=thirty_days_ago)
                )
            else:

                thirty_days_ago = timezone.now() - timedelta(days=30)
                queryset = queryset.filter(
                    Q(last_login__lt=thirty_days_ago) | Q(last_login__isnull=True),
                    created__lt=thirty_days_ago,
                )

        exclude_staff = (
            self.request.query_params.get("exclude_staff", "").lower() == "true"
        )
        if exclude_staff:
            queryset = queryset.filter(is_staff=False)

        inactive_only = (
            self.request.query_params.get("inactive_only", "").lower() == "true"
        )
        if inactive_only:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(
                Q(last_login__lt=thirty_days_ago) | Q(last_login__isnull=True),
                created__lt=thirty_days_ago,
            )

        never_logged_in = (
            self.request.query_params.get("never_logged_in", "").lower() == "true"
        )
        if never_logged_in:
            queryset = queryset.filter(last_login__isnull=True)

        has_logged_in = (
            self.request.query_params.get("has_logged_in", "").lower() == "true"
        )
        if has_logged_in:
            queryset = queryset.filter(last_login__isnull=False)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(fullname__icontains=search)
                | Q(username__icontains=search)
            )

        return queryset

    @api_error_handler
    @dynamic_rate_limit(default_rate=3, default_period=900)
    @extend_schema(
        description="Export users data as CSV or JSON",
        parameters=[
            OpenApiParameter(
                name="format",
                description="Export format ('csv' or 'json'), defaults to 'csv'",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="search",
                description="Search by username, email, fullname, or role",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="role",
                description="Filter by user role",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="email",
                description="Filter by email (contains)",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="email_exact",
                description="Filter by exact email match",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="email_domain",
                description="Filter by email domain",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="username",
                description="Filter by username (contains)",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="is_active",
                description="Filter by active status",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="exclude_staff",
                description="Exclude staff users",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="inactive_only",
                description="Include only inactive users",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="never_logged_in",
                description="Filter to users who have never logged in",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="has_logged_in",
                description="Filter to users who have logged in",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
            OpenApiParameter(
                name="include_superusers",
                description="Include superuser accounts",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                default=None,
            ),
        ],
        responses={
            200: {
                "description": "Users data exported successfully",
                "content": {
                    "text/csv": {"schema": {"type": "string", "format": "binary"}},
                    "application/json": {
                        "schema": {"type": "string", "format": "binary"}
                    },
                },
            },
            400: _("Bad Request"),
            403: {"description": "Permission denied"},
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Export users data as CSV or JSON based on the format parameter.
        """

        export_format = request.query_params.get("format", "csv").lower()
        queryset = self.get_queryset()
        record_count = queryset.count()

        audit_logger.warning(
            "USER_DATA_EXPORT_ATTEMPT",
            extra={
                "user_id": str(request.user.id),
                "username": request.user.username,
                "user_role": request.user.role,
                "export_format": export_format,
                "record_count": record_count,
                "filter_params": dict(request.query_params),
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "timestamp": timezone.now().isoformat(),
            },
        )

        if record_count > 1000:
            audit_logger.critical(
                "LARGE_USER_DATA_EXPORT",
                extra={
                    "user_id": str(request.user.id),
                    "record_count": record_count,
                    "timestamp": timezone.now().isoformat(),
                },
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        serializer = UserExportSerializer(
            queryset, many=True, context={"request": request}
        )

        if export_format == "json":
            response = HttpResponse(content_type="application/json")

            filename = request.query_params.get("filename", "users.json")

            import re

            filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
            filename = filename.replace("..", "_")
            if not filename.endswith(".json"):
                filename = f"{filename.split('.')[0]}.json"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            json.dump(serializer.data, response, cls=CustomJSONEncoder, indent=2)
            return response

        response = HttpResponse(content_type="text/csv")

        filename = request.query_params.get("filename", "users.csv")
        import re

        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = filename.replace("..", "_")
        if not filename.endswith(".csv"):
            filename = f"{filename.split('.')[0]}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        header = [
            "ID",
            "Username",
            "Email",
            "Full Name",
            "Role",
            "Staff",
            "Created At",
            "Phone Number",
        ]
        writer.writerow(header)

        for user_data in serializer.data:
            row = [
                sanitize_csv_field(user_data.get("id", "")),
                sanitize_csv_field(user_data.get("username", "")),
                sanitize_csv_field(user_data.get("email", "")),
                sanitize_csv_field(user_data.get("fullname", "")),
                sanitize_csv_field(user_data.get("role", "")),
                sanitize_csv_field("Yes" if user_data.get("is_staff", False) else "No"),
                sanitize_csv_field(user_data.get("created_at", "")),
                sanitize_csv_field(user_data.get("phone_number", "")),
            ]
            writer.writerow(row)

        return response
