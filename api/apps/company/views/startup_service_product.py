from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.company.models import StartupServiceProduct, StartupProfile
from apps.company.serializers.startup_profile import (
    StartupServiceProductSerializer,
)
from core.permissions import StartupAccessPermission, IsFounderOrMember


@extend_schema_view(
    list=extend_schema(
        tags=["Companies"], 
        summary="List services/products",
        description="Retrieve a list of startup services and products. For founders, only shows their own startup's services/products."
    ),
    retrieve=extend_schema(
        tags=["Companies"], 
        summary="Get service/product",
        description="Retrieve details of a specific service/product"
    ),
    create=extend_schema(
        tags=["Companies"], 
        summary="Create service/product",
        description="Create a new service/product for a startup. Requires startup ID in the request body.",
        examples=[
            {
                "startup": "123e4567-e89b-12d3-a456-426614174000",
                "name": "AI-Powered Analytics Platform",
                "description": "Advanced analytics solution for e-commerce businesses",
                "is_active": True
            }
        ]
    ),
    update=extend_schema(
        tags=["Companies"], 
        summary="Update service/product",
        description="Update an existing service/product"
    ),
    partial_update=extend_schema(
        tags=["Companies"], 
        summary="Patch service/product",
        description="Partially update a service/product"
    ),
    destroy=extend_schema(
        tags=["Companies"], 
        summary="Delete service/product",
        description="Delete a service/product"
    ),
)
class StartupServiceProductViewSet(viewsets.ModelViewSet):
    queryset = StartupServiceProduct.objects.select_related("startup").all()
    serializer_class = StartupServiceProductSerializer

    # Use object-level founder/member permission so owners can modify (200),
    # and non-owners get 403 instead of 404
    permission_classes = [IsAuthenticated, IsFounderOrMember]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin":
            return qs
        role = getattr(user, "role", "")
        if role == "founder":
            # Allow visibility; object-level permission controls writes
            return qs
        if role == "reviewer":
            return qs

        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        from rest_framework import serializers
        startup_id = self.request.data.get("startup")
        if not startup_id:
            raise serializers.ValidationError({"startup": ["This field is required."]})
        try:
            startup = StartupProfile.objects.get(id=startup_id)
        except StartupProfile.DoesNotExist:
            raise serializers.ValidationError({"startup": ["Invalid startup id."]})


        if not (getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin"):
            if startup.primary_founder_id != getattr(user, "id", None):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You can only add products to your own startup.")

        serializer.save(startup=startup)


