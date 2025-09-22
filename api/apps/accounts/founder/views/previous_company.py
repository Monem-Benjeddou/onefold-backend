from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django.db import models

from apps.accounts.founder.models import PreviousCompany
from apps.accounts.founder.serializers import (
    PreviousCompanySerializer,
    PreviousCompanyCreateSerializer,
    PreviousCompanyUpdateSerializer
)


class PreviousCompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing previous company records.
    
    Provides CRUD operations for founder's previous work experience.
    """
    
    queryset = PreviousCompany.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'position', 'industry']
    ordering_fields = ['start_date', 'end_date', 'created']
    ordering = ['-end_date', '-start_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return PreviousCompanyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PreviousCompanyUpdateSerializer
        return PreviousCompanySerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        

        if not self.request.user.is_staff:
            queryset = queryset.filter(founder__user=self.request.user)
        
        return queryset.select_related('founder', 'founder__user')
    
    @action(detail=False, methods=['get'])
    def my_companies(self, request):
        """Get the current user's previous company records."""
        try:
            founder_profile = request.user.founder_profile
            companies = founder_profile.previous_companies.all()
            serializer = self.get_serializer(companies, many=True)
            return Response(serializer.data)
        except:
            return Response(
                {'detail': 'Founder profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def current_companies(self, request):
        """Get current company records."""
        queryset = self.get_queryset().filter(is_current=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed_companies(self, request):
        """Get completed company records."""
        queryset = self.get_queryset().filter(
            models.Q(end_date__isnull=False) & 
            models.Q(is_current=False)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_company_type(self, request):
        """Get companies filtered by type."""
        company_type = request.query_params.get('type', None)
        if company_type:
            queryset = self.get_queryset().filter(company_type=company_type)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Company type parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
