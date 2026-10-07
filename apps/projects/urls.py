from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.verification.views import ProjectCheckListCreateView

from .views import ProjectViewSet

app_name = "projects"

router = DefaultRouter()
router.register("", ProjectViewSet, basename="project")

urlpatterns = [
    path(
        "<uuid:project_id>/checks/",
        ProjectCheckListCreateView.as_view(),
        name="project-checks",
    ),
    path("", include(router.urls)),
]
