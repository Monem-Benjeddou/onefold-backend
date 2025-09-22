from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.company.models import CompanyMember
from apps.company.serializers import (
    CompanyMemberSerializer,
    CompanyMemberCreateSerializer,
    CompanyMemberUpdateSerializer
)


class CompanyMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing company members.
    
    Provides CRUD operations for startup team members.
    """
    
    queryset = CompanyMember.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['position', 'description', 'user__full_name']
    ordering_fields = ['start_date', 'end_date', 'created']
    ordering = ['-is_current', 'member_type', 'position']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return CompanyMemberCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CompanyMemberUpdateSerializer
        return CompanyMemberSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        

        if not self.request.user.is_staff:
            queryset = queryset.filter(startup__primary_founder=self.request.user)
        
        return queryset.select_related('user', 'startup')
    
    @action(detail=False, methods=['get'])
    def my_memberships(self, request):
        """Get the current user's company memberships."""
        memberships = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current_members(self, request):
        """Get all current company members."""
        queryset = self.get_queryset().filter(is_current=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_member_type(self, request):
        """Get members filtered by member type."""
        member_type = request.query_params.get('type', None)
        if member_type:
            queryset = self.get_queryset().filter(member_type=member_type)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Member type parameter is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def primary_contacts(self, request):
        """Get all primary contacts."""
        queryset = self.get_queryset().filter(is_primary_contact=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
