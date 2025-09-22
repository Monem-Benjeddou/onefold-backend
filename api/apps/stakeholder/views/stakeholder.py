from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.stakeholder.models import Stakeholder
from apps.stakeholder.serializers import (
    StakeholderSerializer,
    StakeholderCreateSerializer,
    StakeholderUpdateSerializer
)


class StakeholderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stakeholders.
    
    Provides CRUD operations for startup stakeholders.
    """
    
    queryset = Stakeholder.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'role_title', 'company_name', 'description']
    ordering_fields = ['influence_level', 'stakeholder_type', 'created']
    ordering = ['-influence_level', 'stakeholder_type', 'full_name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return StakeholderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StakeholderUpdateSerializer
        return StakeholderSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show stakeholders of their startups
        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup')
    
    @action(detail=False, methods=['get'])
    def my_stakeholders(self, request):
        """Get the current user's startup stakeholders."""
        stakeholders = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(stakeholders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get stakeholders filtered by type."""
        stakeholder_type = request.query_params.get('type', None)
        if stakeholder_type:
            queryset = self.get_queryset().filter(stakeholder_type=stakeholder_type)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Stakeholder type parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def investors(self, request):
        """Get all investor stakeholders."""
        queryset = self.get_queryset().filter(stakeholder_type='investor')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def advisors(self, request):
        """Get all advisor stakeholders."""
        queryset = self.get_queryset().filter(stakeholder_type='advisor')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def partners(self, request):
        """Get all partner stakeholders."""
        queryset = self.get_queryset().filter(stakeholder_type='partner')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_influence(self, request):
        """Get all high influence stakeholders."""
        queryset = self.get_queryset().filter(influence_level='high')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
