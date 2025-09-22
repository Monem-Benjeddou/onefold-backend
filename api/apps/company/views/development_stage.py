from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import filters
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.company.models import DevelopmentStage
from apps.company.serializers import (
    DevelopmentStageSerializer,
    DevelopmentStageCreateSerializer,
    DevelopmentStageUpdateSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List development stages",
        description="Retrieve a list of all development stages with filtering capabilities.",
        tags=["Companies"],
    ),
    create=extend_schema(
        summary="Create development stage",
        description="Create a new development stage (admin only).",
        tags=["Companies"],
    ),
    retrieve=extend_schema(
        summary="Retrieve development stage",
        description="Get detailed information about a specific development stage.",
        tags=["Companies"],
    ),
    update=extend_schema(
        summary="Update development stage",
        description="Update an existing development stage (admin only).",
        tags=["Companies"],
    ),
    partial_update=extend_schema(
        summary="Partially update development stage",
        description="Partially update an existing development stage (admin only).",
        tags=["Companies"],
    ),
    destroy=extend_schema(
        summary="Delete development stage",
        description="Delete a development stage permanently (admin only).",
        tags=["Companies"],
    ),
)
class DevelopmentStageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing development stages.
    
    Provides CRUD operations for development stages.
    Admin-only for create/update/delete operations.
    """
    
    queryset = DevelopmentStage.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created']
    ordering = ['order', 'name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return DevelopmentStageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DevelopmentStageUpdateSerializer
        return DevelopmentStageSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        summary="Get active development stages",
        description="Retrieve all active development stages.",
        tags=["Companies"],
        responses={200: DevelopmentStageSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def active_stages(self, request):
        """Get all active development stages."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Activate development stage",
        description="Activate a development stage (admin only).",
        tags=["Companies"],
        responses={200: DevelopmentStageSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a development stage (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stage = self.get_object()
        stage.is_active = True
        stage.save()
        
        serializer = self.get_serializer(stage)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Deactivate development stage",
        description="Deactivate a development stage (admin only).",
        tags=["Companies"],
        responses={200: DevelopmentStageSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a development stage (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stage = self.get_object()
        stage.is_active = False
        stage.save()
        
        serializer = self.get_serializer(stage)
        return Response(serializer.data)
