from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.company.models import StartupServiceProduct, StartupProfile
from apps.company.serializers.startup_profile import (
    StartupServiceProductSerializer,
)
from core.permissions import StartupAccessPermission


@extend_schema_view(
    list=extend_schema(tags=["Companies"], summary="List services/products"),
    retrieve=extend_schema(tags=["Companies"], summary="Get service/product"),
    create=extend_schema(tags=["Companies"], summary="Create service/product"),
    update=extend_schema(tags=["Companies"], summary="Update service/product"),
    partial_update=extend_schema(tags=["Companies"], summary="Patch service/product"),
    destroy=extend_schema(tags=["Companies"], summary="Delete service/product"),
)
class StartupServiceProductViewSet(viewsets.ModelViewSet):
    queryset = StartupServiceProduct.objects.select_related("startup").all()
    serializer_class = StartupServiceProductSerializer
    permission_classes = [IsAuthenticated, StartupAccessPermission]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # Admin/staff: full visibility
        if getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin":
            return qs
        role = getattr(user, "role", "")
        if role == "founder":
            # Only own startup items
            return qs.filter(startup__primary_founder=user)
        if role == "reviewer":
            # Read-only visibility to all
            return qs
        # Default: no access
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        startup_id = self.request.data.get("startup")
        if not startup_id:
            return serializer.save()
        try:
            startup = StartupProfile.objects.get(id=startup_id)
        except StartupProfile.DoesNotExist:
            raise ValueError("Invalid startup id")

        # Enforce ownership for founders; admins can create for any
        if not (getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin"):
            if startup.primary_founder_id != getattr(user, "id", None):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You can only add products to your own startup.")

        serializer.save(startup=startup)


