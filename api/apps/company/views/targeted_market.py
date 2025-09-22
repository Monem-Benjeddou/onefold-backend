from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.company.models import TargetedMarket
from apps.company.serializers import (
    TargetedMarketSerializer,
    TargetedMarketCreateSerializer,
    TargetedMarketUpdateSerializer
)


class TargetedMarketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing targeted markets.
    
    Provides CRUD operations for startup target markets.
    """
    
    queryset = TargetedMarket.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['market_name', 'description']
    ordering_fields = ['market_type', 'market_name', 'created']
    ordering = ['-is_primary', 'market_type', 'market_name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return TargetedMarketCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TargetedMarketUpdateSerializer
        return TargetedMarketSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show markets of their startups
        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup')
    
    @action(detail=False, methods=['get'])
    def my_markets(self, request):
        """Get the current user's startup target markets."""
        markets = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(markets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_market_type(self, request):
        """Get markets filtered by market type."""
        market_type = request.query_params.get('type', None)
        if market_type:
            queryset = self.get_queryset().filter(market_type=market_type)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Market type parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def primary_markets(self, request):
        """Get all primary target markets."""
        queryset = self.get_queryset().filter(is_primary=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def local_markets(self, request):
        """Get all local target markets."""
        queryset = self.get_queryset().filter(market_type='local')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def gcc_markets(self, request):
        """Get all GCC target markets."""
        queryset = self.get_queryset().filter(market_type='gcc')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def global_markets(self, request):
        """Get all global target markets."""
        queryset = self.get_queryset().filter(market_type='global')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
