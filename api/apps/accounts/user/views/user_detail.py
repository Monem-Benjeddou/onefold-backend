from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.models import User
from apps.accounts.user.serializers import UserSerializer


@extend_schema(
    tags=["Users"],
    description="Retrieve user details by user UUID",
)
class UserDetailView(RetrieveAPIView):
    """
    View for retrieving user details by UUID.

    GET: Returns full user information, requires authentication.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
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
    @dynamic_rate_limit(default_rate=60, default_period=60)
    @extend_schema(
        description="Retrieve user details by UUID",
        responses={
            200: UserSerializer,
            404: {"description": "User not found"},
            401: {"description": "Authentication required"},
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve user details by UUID.
        """
        instance = self.get_object()
        if not instance:
            return Response(
                {"error": _("User not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
