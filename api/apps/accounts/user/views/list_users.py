from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils.translation import gettext_lazy as _

from core.abstract.paginations import MetaPageNumberPagination
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.serializers import UserSerializer
from apps.accounts.user.models import User
from apps.accounts.user.filters.admin_filters import UserFilter
from apps.accounts.user.permissions import IsBusinessAdminOrNeoAdmin


@extend_schema(tags=["Admin"])
class ListUsersView(ListAPIView):
    """
    View for listing users with filtering options.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsBusinessAdminOrNeoAdmin]
    pagination_class = MetaPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = UserFilter
    search_fields = [
        "username",
        "email",
        "fullname",
        "role",
    ]
    ordering_fields = ["username", "email", "created", "role"]
    ordering = ["-created"]

    def get_queryset(self):
        """
        Get the list of users, excluding superusers unless
        explicitly requested by a superuser.
        Optimized with select_related to prevent N+1 queries.
        """
        from django.db.models import Case, When, Value, BooleanField, Q
        from django.utils import timezone

        queryset = User.objects.select_related("country", "banned_by").annotate(
            is_currently_banned=Case(
                When(
                    Q(is_banned=True)
                    & (
                        Q(ban_expires_at__isnull=True)
                        | Q(ban_expires_at__gt=timezone.now())
                    ),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            is_account_active=Case(
                When(Q(is_banned=False) & Q(is_deactivated=False), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )

        include_superusers = (
            self.request.query_params.get("include_superusers", "false").lower()
            == "true"
        )

        if not include_superusers and not self.request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)

        return queryset

    @api_error_handler
    @dynamic_rate_limit(default_rate=20, default_period=60)
    @extend_schema(
        description="List all users with filtering and search options",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search by username, email, fullname, or role",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="role",
                description="Filter by user role",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                explode=True,
            ),
            OpenApiParameter(
                name="include_superusers",
                description="Include superuser accounts in results (default: false)",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                default=False,
            ),
            OpenApiParameter(
                name="is_active",
                description=_("Filter by active status"),
                required=False,
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses={200: UserSerializer(many=True), 400: _("Bad Request")},
    )
    def get(self, request, *args, **kwargs):
        """
        List users with optional filtering.
        """
        return self.list(request, *args, **kwargs)
