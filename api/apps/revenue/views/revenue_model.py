from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import filters
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.revenue.models import RevenueModel, StartupRevenueModel
from apps.revenue.serializers import (
    RevenueModelSerializer,
    RevenueModelCreateSerializer,
    RevenueModelUpdateSerializer,
    StartupRevenueModelCreateSerializer,
    StartupRevenueModelUpdateSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List revenue models",
        description="Retrieve a list of all revenue models with filtering capabilities.",
        tags=["Revenue"],
    ),
    create=extend_schema(
        summary="Create revenue model",
        description="Create a new revenue model (admin only).",
        tags=["Revenue"],
    ),
    retrieve=extend_schema(
        summary="Retrieve revenue model",
        description="Get detailed information about a specific revenue model.",
        tags=["Revenue"],
    ),
    update=extend_schema(
        summary="Update revenue model",
        description="Update an existing revenue model (admin only).",
        tags=["Revenue"],
    ),
    partial_update=extend_schema(
        summary="Partially update revenue model",
        description="Partially update an existing revenue model (admin only).",
        tags=["Revenue"],
    ),
    destroy=extend_schema(
        summary="Delete revenue model",
        description="Delete a revenue model permanently (admin only).",
        tags=["Revenue"],
    ),
)
class RevenueModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing revenue models.
    
    Provides CRUD operations for revenue models.
    Admin-only for create/update/delete operations.
    """
    
    queryset = RevenueModel.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created']
    ordering = ['order', 'name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return RevenueModelCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RevenueModelUpdateSerializer
        return RevenueModelSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        summary="Get active revenue models",
        description="Retrieve all active revenue models.",
        tags=["Revenue"],
        responses={200: RevenueModelSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def active_models(self, request):
        """Get all active revenue models."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Activate revenue model",
        description="Activate a revenue model (admin only).",
        tags=["Revenue"],
        responses={200: RevenueModelSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a revenue model (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        model = self.get_object()
        model.is_active = True
        model.save()
        
        serializer = self.get_serializer(model)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Deactivate revenue model",
        description="Deactivate a revenue model (admin only).",
        tags=["Revenue"],
        responses={200: RevenueModelSerializer, 403: {"description": "Permission denied"}},
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a revenue model (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        model = self.get_object()
        model.is_active = False
        model.save()
        
        serializer = self.get_serializer(model)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Assign revenue model to startup",
        description="Assign a revenue model to a specific startup.",
        tags=["Revenue"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'startup_id': {'type': 'string', 'description': 'UUID of the startup'},
                    'is_primary': {'type': 'boolean', 'description': 'Whether this is the primary revenue model'},
                    'percentage': {'type': 'number', 'description': 'Percentage of revenue from this model'},
                    'description': {'type': 'string', 'description': 'Additional description'},
                },
                'required': ['startup_id'],
            }
        },
        responses={
            201: StartupRevenueModelCreateSerializer,
            400: {"description": "Startup ID is required or model already assigned"},
        },
    )
    @action(detail=True, methods=['post'])
    def assign_to_startup(self, request, pk=None):
        """Assign revenue model to a startup."""
        revenue_model = self.get_object()
        startup_id = request.data.get('startup_id')
        is_primary = request.data.get('is_primary', False)
        percentage = request.data.get('percentage', None)
        description = request.data.get('description', '')
        
        if not startup_id:
            return Response(
                {'detail': 'Startup ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if assignment already exists
        if StartupRevenueModel.objects.filter(
            startup_id=startup_id, 
            revenue_model=revenue_model
        ).exists():
            return Response(
                {'detail': 'This revenue model is already assigned to the startup.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the assignment
        assignment = StartupRevenueModel.objects.create(
            startup_id=startup_id,
            revenue_model=revenue_model,
            is_primary=is_primary,
            percentage=percentage,
            description=description
        )
        
        serializer = StartupRevenueModelCreateSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
