from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.revenue.models import RevenueStream
from apps.revenue.serializers import (
    RevenueStreamSerializer,
    RevenueStreamCreateSerializer,
    RevenueStreamUpdateSerializer
)


class RevenueStreamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing revenue streams.
    
    Provides CRUD operations for startup revenue streams.
    """
    
    queryset = RevenueStream.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['revenue_percentage', 'name', 'created']
    ordering = ['-revenue_percentage', 'name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return RevenueStreamCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RevenueStreamUpdateSerializer
        return RevenueStreamSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show revenue streams of their startups
        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('startup')
    
    @action(detail=False, methods=['get'])
    def my_revenue_streams(self, request):
        """Get the current user's startup revenue streams."""
        streams = self.get_queryset().filter(startup__primary_founder=request.user)
        serializer = self.get_serializer(streams, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recurring_streams(self, request):
        """Get all recurring revenue streams."""
        queryset = self.get_queryset().filter(is_recurring=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_streams(self, request):
        """Get all active revenue streams."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_revenue_streams(self, request):
        """Get revenue streams ordered by revenue percentage."""
        queryset = self.get_queryset().filter(
            revenue_percentage__isnull=False
        ).order_by('-revenue_percentage')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def monthly_revenue(self, request):
        """Get revenue streams with monthly revenue data."""
        queryset = self.get_queryset().filter(
            monthly_revenue__isnull=False,
            monthly_revenue__gt=0
        ).order_by('-monthly_revenue')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def annual_revenue(self, request):
        """Get revenue streams with annual revenue data."""
        queryset = self.get_queryset().filter(
            annual_revenue__isnull=False,
            annual_revenue__gt=0
        ).order_by('-annual_revenue')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
