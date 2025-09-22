from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django.db import models

from apps.accounts.founder.models import Education
from apps.accounts.founder.serializers import (
    EducationSerializer,
    EducationCreateSerializer,
    EducationUpdateSerializer
)


class EducationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing education records.
    
    Provides CRUD operations for founder education history.
    """
    
    queryset = Education.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['institution_name', 'degree', 'field_of_study']
    ordering_fields = ['start_date', 'end_date', 'created']
    ordering = ['-end_date', '-start_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return EducationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EducationUpdateSerializer
        return EducationSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own education records
        if not self.request.user.is_staff:
            queryset = queryset.filter(founder__user=self.request.user)
        
        return queryset.select_related('founder', 'founder__user')
    
    @action(detail=False, methods=['get'])
    def my_education(self, request):
        """Get the current user's education records."""
        try:
            founder_profile = request.user.founder_profile
            education = founder_profile.education_history.all()
            serializer = self.get_serializer(education, many=True)
            return Response(serializer.data)
        except:
            return Response(
                {'detail': 'Founder profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def current_education(self, request):
        """Get current education records."""
        queryset = self.get_queryset().filter(is_current=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed_education(self, request):
        """Get completed education records."""
        queryset = self.get_queryset().filter(
            models.Q(end_date__isnull=False) & 
            models.Q(is_current=False)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
