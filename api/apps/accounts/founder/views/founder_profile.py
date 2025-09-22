from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.accounts.founder.models import FounderProfile
from apps.accounts.founder.serializers import (
    FounderProfileSerializer,
    FounderProfileCreateSerializer,
    FounderProfileUpdateSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List founder profiles",
        description="Retrieve a list of all founder profiles with filtering and search capabilities.",
        tags=["Founders"],
    ),
    create=extend_schema(
        summary="Create founder profile",
        description="Create a new founder profile with education and previous company data.",
        tags=["Founders"],
    ),
    retrieve=extend_schema(
        summary="Retrieve founder profile",
        description="Get detailed information about a specific founder profile.",
        tags=["Founders"],
    ),
    update=extend_schema(
        summary="Update founder profile",
        description="Update an existing founder profile with new information.",
        tags=["Founders"],
    ),
    partial_update=extend_schema(
        summary="Partially update founder profile",
        description="Partially update an existing founder profile.",
        tags=["Founders"],
    ),
    destroy=extend_schema(
        summary="Delete founder profile",
        description="Delete a founder profile permanently.",
        tags=["Founders"],
    ),
)
class FounderProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing founder profiles.
    
    Provides CRUD operations for founder profiles with nested education
    and previous company data.
    """
    
    queryset = FounderProfile.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'email_address', 'bio', 'location']
    ordering_fields = ['created', 'updated', 'full_name', 'role']
    ordering = ['-created']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return FounderProfileCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FounderProfileUpdateSerializer
        return FounderProfileSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own profile or public profiles
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                models.Q(user=self.request.user) | 
                models.Q(is_public=True)
            )
        
        return queryset.select_related('user').prefetch_related(
            'education_history', 'previous_companies'
        )
    
    def perform_create(self, serializer):
        """Set the user when creating a founder profile."""
        serializer.save(user=self.request.user)
    
    @extend_schema(
        summary="Get current user's founder profile",
        description="Retrieve the founder profile of the currently authenticated user.",
        tags=["Founders"],
        responses={200: FounderProfileSerializer, 404: {"description": "Founder profile not found"}},
    )
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get the current user's founder profile."""
        try:
            profile = request.user.founder_profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except FounderProfile.DoesNotExist:
            return Response(
                {'detail': 'Founder profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Verify founder profile",
        description="Mark a founder profile as verified (staff only).",
        tags=["Founders"],
        responses={200: FounderProfileSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a founder profile (staff only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        profile = self.get_object()
        profile.is_verified = True
        profile.save()
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Unverify founder profile",
        description="Remove verification from a founder profile (staff only).",
        tags=["Founders"],
        responses={200: FounderProfileSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        """Unverify a founder profile (staff only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        profile = self.get_object()
        profile.is_verified = False
        profile.save()
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
