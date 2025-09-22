from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from django.utils.translation import get_language

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from core.decorators.cache_control import CacheControlMixin
from core.utilities.cache_utils import cache_manager
from core.abstract.paginations import MetaPageNumberPagination
from ..models import Country
from ..serializers import CountryLightSerializer, CountryFullSerializer
from ..filters import CountryFilterSet


@extend_schema(tags=["Countries"])
class CountryListView(CacheControlMixin, generics.ListAPIView):
    """
    API view for listing countries.
    Provides paginated list of countries with filtering and search capabilities.
    """

    queryset = Country.objects.all()
    pagination_class = MetaPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CountryFilterSet
    permission_classes = [AllowAny]
    filterset_fields = ["region", "subregion"]

    cache_timeout = 3600
    cache_key_prefix = "countries_list"
    cache_vary_on_user = False
    cache_vary_on_language = True

    @api_error_handler
    @dynamic_rate_limit(default_rate=30, default_period=60)
    @extend_schema(
        description="List of countries. Use 'full=true' to get full country details, and 'pagination=false' to disable pagination.",
        responses={
            200: CountryLightSerializer(many=True),
            429: {"description": _("Too Many Requests")},
        },
        parameters=[
            OpenApiParameter(
                name="full",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Return full country details",
            ),
            OpenApiParameter(
                name="pagination",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Disable pagination if set to false",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number for paginated results",
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of items per page",
            ),
        ],
    )
    def get(self, request: Request, *args, **kwargs):
        """
        Retrieve a paginated list of countries.

        Supports caching, full/light serialization modes, and optional pagination.
        Returns countries ordered by name with filtering and search capabilities.
        """
        full = request.query_params.get("full", "false").lower() == "true"
        pagination = request.query_params.get("pagination", "true").lower() == "true"

        cached_response = self.get_cached_response(request, *args, **kwargs)
        if cached_response:
            return cached_response

        if not pagination:
            self.pagination_class = None

        response = super().get(request, *args, **kwargs)

        self.set_cached_response(request, response, *args, **kwargs)

        return response

    def get_serializer_class(self):
        """Return appropriate serializer class based on 'full' parameter."""
        if (
            self.request
            and hasattr(self.request, "query_params")
            and self.request.query_params.get("full") == "true"
        ):
            return CountryFullSerializer
        return CountryLightSerializer
