from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """A builder's own projects. Other people's projects are never visible here."""

    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        return Project.objects.filter(user=self.request.user)
