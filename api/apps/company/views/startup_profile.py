from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.company.models import StartupProfile
from apps.company.serializers import (
    StartupProfileSerializer,
    StartupProfileCreateSerializer,
    StartupProfileUpdateSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List startup profiles",
        description="Retrieve a list of all startup profiles with filtering and search capabilities.",
        tags=["Companies"],
    ),
    create=extend_schema(
        summary="Create startup profile",
        description="Create a new startup profile with team members and target markets.",
        tags=["Companies"],
    ),
    retrieve=extend_schema(
        summary="Retrieve startup profile",
        description="Get detailed information about a specific startup profile.",
        tags=["Companies"],
    ),
    update=extend_schema(
        summary="Update startup profile",
        description="Update an existing startup profile with new information.",
        tags=["Companies"],
    ),
    partial_update=extend_schema(
        summary="Partially update startup profile",
        description="Partially update an existing startup profile.",
        tags=["Companies"],
    ),
    destroy=extend_schema(
        summary="Delete startup profile",
        description="Delete a startup profile permanently.",
        tags=["Companies"],
    ),
)
class StartupProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing startup profiles.
    
    Provides CRUD operations for startup profiles with nested relationships.
    """
    
    queryset = StartupProfile.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'startup_name', 'startup_industry', 'location', 'bio', 
        'services_and_products'
    ]
    ordering_fields = ['created', 'updated', 'startup_name', 'founded_year']
    ordering = ['-created']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return StartupProfileCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StartupProfileUpdateSerializer
        return StartupProfileSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own startups or public ones
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                models.Q(primary_founder=self.request.user) | 
                models.Q(is_public=True)
            )
        
        return queryset.select_related('primary_founder').prefetch_related(
            'members__user', 'targeted_markets', 'development_stage__stage'
        )
    
    @extend_schema(
        summary="Get current user's startups",
        description="Retrieve all startup profiles owned by the currently authenticated user.",
        tags=["Companies"],
        responses={200: StartupProfileSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def my_startups(self, request):
        """Get the current user's startup profiles."""
        startups = self.get_queryset().filter(primary_founder=request.user)
        serializer = self.get_serializer(startups, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Verify startup profile",
        description="Mark a startup profile as verified (staff only).",
        tags=["Companies"],
        responses={200: StartupProfileSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a startup profile (staff only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        startup = self.get_object()
        startup.is_verified = True
        startup.save()
        
        serializer = self.get_serializer(startup)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Unverify startup profile",
        description="Remove verification from a startup profile (staff only).",
        tags=["Companies"],
        responses={200: StartupProfileSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        """Unverify a startup profile (staff only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        startup = self.get_object()
        startup.is_verified = False
        startup.save()
        
        serializer = self.get_serializer(startup)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get startups by industry",
        description="Filter startups by industry name.",
        tags=["Companies"],
        parameters=[
            OpenApiParameter(
                name="industry",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Industry name to filter by",
                required=True,
            ),
        ],
        responses={200: StartupProfileSerializer(many=True), 400: {"description": "Industry parameter is required"}},
    )
    @action(detail=False, methods=['get'])
    def by_industry(self, request):
        """Get startups filtered by industry."""
        industry = request.query_params.get('industry', None)
        if industry:
            queryset = self.get_queryset().filter(startup_industry__icontains=industry)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Industry parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        summary="Get startups by location",
        description="Filter startups by location.",
        tags=["Companies"],
        parameters=[
            OpenApiParameter(
                name="location",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Location to filter by",
                required=True,
            ),
        ],
        responses={200: StartupProfileSerializer(many=True), 400: {"description": "Location parameter is required"}},
    )
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get startups filtered by location."""
        location = request.query_params.get('location', None)
        if location:
            queryset = self.get_queryset().filter(location__icontains=location)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Location parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        summary="Get verified startups",
        description="Retrieve all verified startup profiles.",
        tags=["Companies"],
        responses={200: StartupProfileSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def verified_startups(self, request):
        """Get all verified startup profiles."""
        queryset = self.get_queryset().filter(is_verified=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
