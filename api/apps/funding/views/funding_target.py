from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.funding.models import FundingTarget
from apps.funding.serializers import (
    FundingTargetSerializer,
    FundingTargetCreateSerializer,
    FundingTargetUpdateSerializer
)


class FundingTargetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing funding targets.
    
    Provides CRUD operations for startup funding targets.
    """
    
    queryset = FundingTarget.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['use_of_funds', 'timeline']
    ordering_fields = ['target_amount', 'pre_money_valuation', 'created']
    ordering = ['-created']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return FundingTargetCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FundingTargetUpdateSerializer
        return FundingTargetSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        

        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup')
    
    @action(detail=False, methods=['get'])
    def my_funding_targets(self, request):
        """Get the current user's startup funding targets."""
        targets = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(targets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_funding_round(self, request):
        """Get funding targets filtered by funding round."""
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
    def active_targets(self, request):
        """Get all active funding targets."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def seed_stage(self, request):
        """Get all seed stage funding targets."""
        queryset = self.get_queryset().filter(funding_round='seed')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def series_a(self, request):
        """Get all Series A funding targets."""
        queryset = self.get_queryset().filter(funding_round='series_a')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_value_targets(self, request):
        """Get funding targets with high target amounts."""
        queryset = self.get_queryset().filter(
            target_amount__isnull=False,
            target_amount__gte=1000000
        ).order_by('-target_amount')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
