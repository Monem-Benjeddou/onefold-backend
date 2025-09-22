from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.serializers import UpdateUserSerializer, UserSerializer
from apps.accounts.user.models import User
from apps.accounts.user.permissions import IsBusinessAdminOrNeoAdmin


@extend_schema(tags=["Admin"])
class UpdateUserView(UpdateAPIView):
    """
    View for updating a user.
    """

    serializer_class = UpdateUserSerializer
    permission_classes = [IsAuthenticated, IsBusinessAdminOrNeoAdmin]
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_object(self):
        """
        Override to properly handle 404 not found errors
        """
        try:
            obj = super().get_object()
            return obj
        except Http404:
            return None

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    @extend_schema(
        description="""
        Update user information including role.
        
        Available roles:
        - user: Regular user
        - admin: Administrator with elevated privileges
        - moderator: Platform moderator
        - influencer: Content creator
        - service: Service provider
        - manufacturer: Manufacturer
        - collector: Collector
        - issuer: Card/NFT issuer
        """,
        request=UpdateUserSerializer,
        responses={200: UserSerializer, 400: _("Bad Request"), 404: _("Not Found")},
    )
    def put(self, request, *args, **kwargs):
        """
        Update a user with the provided data.
        """
        instance = self.get_object()
        if not instance:
            return Response(
                {"error": _("User not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    @extend_schema(
        description="""
        Partially update user information including role.
        
        Available roles:
        - user: Regular user
        - admin: Administrator with elevated privileges
        - moderator: Platform moderator
        - influencer: Content creator
        - service: Service provider
        - manufacturer: Manufacturer
        - collector: Collector
        - issuer: Card/NFT issuer
        """,
        request=UpdateUserSerializer,
        responses={200: UserSerializer, 400: _("Bad Request"), 404: _("Not Found")},
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update a user with the provided data.
        """
        instance = self.get_object()
        if not instance:
            return Response(
                {"error": _("User not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
