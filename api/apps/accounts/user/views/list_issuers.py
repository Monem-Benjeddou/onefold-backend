from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.utils.translation import gettext_lazy as _

from core.abstract.paginations import MetaPageNumberPagination
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
# Issuer functionality removed
from apps.accounts.user.serializers import UserSerializer
from apps.accounts.user.models import User
from apps.accounts.user.permissions import IsCardCreatorOrAdmin


@extend_schema(tags=["Users", "Issuers", "Card creation"])
class ListIssuersView(ListAPIView):
    """
    View for listing issuer users with filtering and search options.

    **Permissions**: Only card creators, admins, and superusers can access this endpoint.

    **Features**:
    - Returns only users with 'issuer' role
    - Comprehensive filtering and search capabilities
    - Pagination with MetaPageNumberPagination
    - Rate limiting for security
    - Full DRF filtering backend support

    **Filtering Options**:
    - Search by username, email, fullname
    - Filter by active status, email verification status
    - Filter by creation date range
    - Order by various fields

    **Rate Limiting**: 30 requests per minute per user
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsCardCreatorOrAdmin]
    pagination_class = MetaPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = None
    search_fields = [
        "username",
        "email",
        "fullname",
        "phone_number",
    ]
    ordering_fields = [
        "username",
        "email",
        "fullname",
        "created",
        "is_active",
        "is_email_verified",
        "phone_number",
    ]
    ordering = ["-created"]

    def get_queryset(self):
        """
        Get optimized queryset for issuer users with all necessary joins and annotations.

        Returns:
            QuerySet: Optimized queryset with performance enhancements and metrics
        """
        return User.objects.none()

    @api_error_handler
    @dynamic_rate_limit(default_rate=30, default_period=60)
    @extend_schema(
        summary="List issuer users (removed)",
        description="""
        Retrieve a paginated list of all issuer users in the system.
        
        **Access Control**:
        - Only accessible by card creators, admins, and superusers
        - Returns only users with 'issuer' role
        
        **Features**:
        - Search across username, email, fullname, and phone number
        - Filter by various user attributes
        - Sort by multiple fields
        - Paginated results with metadata
        
        **Use Cases**:
        - Managing issuer accounts
        - Selecting issuers for card assignments
        - Administrative oversight of issuer users
        """,
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search across email, username, fullname, phone number, and company name",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="is_active",
                description="Filter by active status",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="is_banned",
                description="Filter by banned status",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="is_verified",
                description="Filter by verified status (blue checkmark)",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="is_email_verified",
                description="Filter by email verification status",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="created_after",
                description="Filter users created after this date (YYYY-MM-DD)",
                required=False,
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="created_before",
                description="Filter users created before this date (YYYY-MM-DD)",
                required=False,
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="email",
                description="Filter by email containing this text",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="username",
                description="Filter by username containing this text",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="fullname",
                description="Filter by fullname containing this text",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="company_name",
                description="Filter by company name containing this text",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="country",
                description="Filter by country ID",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="has_company_info",
                description="Filter users who have company information",
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="issued_cards_count_min",
                description="Filter users with at least this many issued cards",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="total_orders_min",
                description="Filter users with at least this many orders",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="ordering",
                description="Order results by field(s). Prefix with '-' for descending order",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample("created_desc", value="-created"),
                    OpenApiExample("email_asc", value="email"),
                    OpenApiExample("name_asc", value="fullname"),
                    OpenApiExample("orders_desc", value="-total_orders"),
                    OpenApiExample("cards_desc", value="-issued_cards_count"),
                ],
            ),
            OpenApiParameter(
                name="page",
                description="Page number for pagination",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                default=1,
            ),
            OpenApiParameter(
                name="limit",
                description="Number of results per page (max 1000)",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                default=5,
            ),
        ],
        responses={
            200: UserSerializer(many=True),
            400: _("Bad Request - Invalid query parameters"),
            401: _("Unauthorized - Authentication required"),
            403: _("Forbidden - Card creator, admin, or superuser access required"),
            429: _("Too Many Requests - Rate limit exceeded"),
        },
    )
    def get(self, request, *args, **kwargs):
        """
        List issuer users with filtering and search capabilities.

        Args:
            request: HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            Response: Paginated list of issuer users with metadata
        """
        return self.list(request, *args, **kwargs)
