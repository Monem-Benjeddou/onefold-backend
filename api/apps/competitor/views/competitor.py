from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.competitor.models import Competitor
from apps.competitor.serializers import (
    CompetitorSerializer,
    CompetitorCreateSerializer,
    CompetitorUpdateSerializer
)


class CompetitorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing competitors.
    
    Provides CRUD operations for startup competitors.
    """
    
    queryset = Competitor.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['competitor_name', 'description', 'location']
    ordering_fields = ['threat_level', 'competitor_type', 'competitor_name', 'created']
    ordering = ['-threat_level', 'competitor_type', 'competitor_name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return CompetitorCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CompetitorUpdateSerializer
        return CompetitorSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        

        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup')
    
    @action(detail=False, methods=['get'])
    def my_competitors(self, request):
        """Get the current user's startup competitors."""
        competitors = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(competitors, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get competitors filtered by type."""
        competitor_type = request.query_params.get('type', None)
        if competitor_type:
            queryset = self.get_queryset().filter(competitor_type=competitor_type)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Competitor type parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def local_competitors(self, request):
        """Get all local competitors."""
        queryset = self.get_queryset().filter(competitor_type='local')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def gcc_competitors(self, request):
        """Get all GCC competitors."""
        queryset = self.get_queryset().filter(competitor_type='gcc')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def global_competitors(self, request):
        """Get all global competitors."""
        queryset = self.get_queryset().filter(competitor_type='global')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_threat(self, request):
        """Get all high threat competitors."""
        queryset = self.get_queryset().filter(threat_level='high')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_threat_level(self, request):
        """Get competitors filtered by threat level."""
        threat_level = request.query_params.get('level', None)
        if threat_level:
            queryset = self.get_queryset().filter(threat_level=threat_level)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Threat level parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
