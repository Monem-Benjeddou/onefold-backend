from django.contrib import admin
from django.urls import include, path
from api.core.health import health_view
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers


class RootResponseSerializer(serializers.Serializer):
    """Serializer for root endpoint response."""
    name = serializers.CharField()
    docs = serializers.CharField()
    schema = serializers.CharField()


@api_view(["GET"]) 
def root_view(_request):
    return Response({"name": "Noev API", "docs": "/api/docs/", "schema": "/api/schema/"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_view),
    path("", root_view),
    # OAuth2 / Social OAuth namespaces required by drf_social_oauth2
    path("o/", include(("oauth2_provider.urls", "oauth2_provider"), namespace="oauth2_provider")),
    path("auth/", include(("drf_social_oauth2.urls", "drf_social_oauth2"), namespace="drf")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema.yaml", SpectacularAPIView.as_view(), name="schema-yaml"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API endpoints
    path("api/v1/auth/", include("api.apps.accounts.auth.urls")),
    path("api/v1/founders/", include("api.apps.accounts.founder.urls")),
    path("api/v1/companies/", include("api.apps.company.urls")),
    path("api/v1/users/", include("api.apps.accounts.user.urls")),
    path("api/v1/stakeholders/", include("api.apps.stakeholder.urls")),
    path("api/v1/competitors/", include("api.apps.competitor.urls")),
    path("api/v1/revenue/", include("api.apps.revenue.urls")),
    path("api/v1/funding/", include("api.apps.funding.urls")),
]


