from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.company.models import StartupDevelopmentStage
from apps.company.serializers import (
    StartupDevelopmentStageSerializer,
    StartupDevelopmentStageCreateSerializer,
    StartupDevelopmentStageUpdateSerializer
)


class StartupDevelopmentStageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing startup development stage assignments.
    
    Provides CRUD operations for linking startups to development stages.
    """
    
    queryset = StartupDevelopmentStage.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['startup__startup_name', 'stage__name', 'notes']
    ordering_fields = ['assigned_date', 'created']
    ordering = ['-assigned_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return StartupDevelopmentStageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StartupDevelopmentStageUpdateSerializer
        return StartupDevelopmentStageSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own startup stages
        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup', 'stage')
    
    @action(detail=False, methods=['get'])
    def my_startup_stages(self, request):
        """Get the current user's startup development stages."""
        stages = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(stages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_stage(self, request):
        """Get startup stages filtered by development stage."""
        stage_id = request.query_params.get('stage_id', None)
        if stage_id:
            queryset = self.get_queryset().filter(stage_id=stage_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Stage ID parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
