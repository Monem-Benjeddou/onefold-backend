from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.views import health, index

urlpatterns = [
    path("", index, name="index"),
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/learning/", include("apps.learning.urls")),
    path("api/v1/projects/", include("apps.projects.urls")),
    path("api/v1/checks/", include("apps.verification.urls")),
]
