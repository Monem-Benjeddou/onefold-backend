from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.stakeholder.models import Investor
from apps.stakeholder.serializers import (
    InvestorSerializer,
    InvestorCreateSerializer,
    InvestorUpdateSerializer
)


class InvestorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing investors.
    
    Provides CRUD operations for detailed investor information.
    """
    
    queryset = Investor.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['person_company_name', 'description']
    ordering_fields = ['investment_date', 'investment_amount', 'created']
    ordering = ['-investment_date', '-investment_amount', 'person_company_name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return InvestorCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InvestorUpdateSerializer
        return InvestorSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show investors of their startups
        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup')
    
    @action(detail=False, methods=['get'])
    def my_investors(self, request):
        """Get the current user's startup investors."""
        investors = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(investors, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_investment_type(self, request):
        """Get investors filtered by investment type."""
        investment_type = request.query_params.get('type', None)
        if investment_type:
            queryset = self.get_queryset().filter(investment_type=investment_type)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Investment type parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def lead_investors(self, request):
        """Get all lead investors."""
        queryset = self.get_queryset().filter(is_lead_investor=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def board_members(self, request):
        """Get all investors with board seats."""
        queryset = self.get_queryset().filter(board_seat=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def angel_investors(self, request):
        """Get all angel investors."""
        queryset = self.get_queryset().filter(investment_type='angel')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vc_investors(self, request):
        """Get all VC investors (Series A and beyond)."""
        queryset = self.get_queryset().filter(
            investment_type__in=['series_a', 'series_b', 'series_c', 'series_d']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
