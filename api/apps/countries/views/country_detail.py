from rest_framework import generics
from rest_framework.response import Response
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request


from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from core.decorators.cache_control import CacheControlMixin
from ..models import Country
from ..serializers import CountryDetailSerializer, CountryLightSerializer


@extend_schema(tags=["Countries"])
class CountryDetailView(CacheControlMixin, generics.RetrieveAPIView):
    """
    API view for retrieving individual country details.
    Provides detailed country information with caching support.
    """

    queryset = Country.objects.all()
    permission_classes = [AllowAny]
    lookup_field = "id"

    cache_timeout = 3600
    cache_key_prefix = "country_detail"
    cache_vary_on_user = False
    cache_vary_on_language = True

    @api_error_handler
    @dynamic_rate_limit(default_rate=60, default_period=60)
    @extend_schema(
        description="Retrieve detailed information about a specific country.",
        responses={
            200: CountryDetailSerializer,
            404: {"description": _("Country not found")},
            429: {"description": _("Too Many Requests")},
        },
    )
    def get(self, request: Request, *args, **kwargs):
        """
        Retrieve detailed information about a specific country.

        Supports caching and full/light serialization modes.
        Returns complete country information including states and timezones.
        """

        cached_response = self.get_cached_response(request, *args, **kwargs)
        if cached_response:
            return cached_response

        response = super().get(request, *args, **kwargs)

        self.set_cached_response(request, response, *args, **kwargs)

        return response

    def get_serializer_class(self):
        """Return appropriate serializer class based on 'full' parameter."""
        if (
            self.request
            and hasattr(self.request, "query_params")
            and self.request.query_params.get("full", "true").lower() == "true"
        ):
            return CountryDetailSerializer
        return CountryLightSerializer
