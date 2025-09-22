from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.funding.models import RaisedFund
from apps.funding.serializers import (
    RaisedFundSerializer,
    RaisedFundCreateSerializer,
    RaisedFundUpdateSerializer
)


class RaisedFundViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing raised funds.
    
    Provides CRUD operations for startup funding records.
    """
    
    queryset = RaisedFund.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['lead_investor', 'participating_investors', 'description']
    ordering_fields = ['funding_date', 'amount_raised', 'created']
    ordering = ['-funding_date', '-amount_raised']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return RaisedFundCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RaisedFundUpdateSerializer
        return RaisedFundSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show raised funds of their startups
        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup')
    
    @action(detail=False, methods=['get'])
    def my_raised_funds(self, request):
        """Get the current user's startup raised funds."""
        funds = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(funds, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_funding_round(self, request):
        """Get raised funds filtered by funding round."""
        funding_round = request.query_params.get('round', None)
        if funding_round:
            queryset = self.get_queryset().filter(funding_round=funding_round)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Funding round parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def announced_funds(self, request):
        """Get all announced funding rounds."""
        queryset = self.get_queryset().filter(is_announced=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unannounced_funds(self, request):
        """Get all unannounced funding rounds."""
        queryset = self.get_queryset().filter(is_announced=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def seed_funding(self, request):
        """Get all seed funding rounds."""
        queryset = self.get_queryset().filter(funding_round='seed')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def series_a_funding(self, request):
        """Get all Series A funding rounds."""
        queryset = self.get_queryset().filter(funding_round='series_a')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_value_funding(self, request):
        """Get funding rounds with high amounts raised."""
        queryset = self.get_queryset().filter(
            amount_raised__gte=1000000  # $1M and above
        ).order_by('-amount_raised')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_funding(self, request):
        """Get recent funding rounds (last 12 months)."""
        from datetime import date, timedelta
        one_year_ago = date.today() - timedelta(days=365)
        
        queryset = self.get_queryset().filter(
            funding_date__gte=one_year_ago
        ).order_by('-funding_date')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def announce(self, request, pk=None):
        """Announce a funding round."""
        funding = self.get_object()
        funding.is_announced = True
        funding.announcement_date = request.data.get('announcement_date')
        funding.save()
        
        serializer = self.get_serializer(funding)
        return Response(serializer.data)
