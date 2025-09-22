from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.models import User
from apps.accounts.profile.serializers import ProfileSerializer


@extend_schema(
    tags=["Users"],
    description="Retrieve user details by user UUID (public access)",
    responses={
        200: ProfileSerializer,
        404: {"description": "User not found"},
    },
)
class RetrieveUserView(RetrieveAPIView):
    """
    View for retrieving user details by UUID.
    Returns full user information, public access (no authentication required).
    """

    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    queryset = User.objects.select_related(
        "country", "influencer_profile"
    ).prefetch_related(
        "influencer_profile__profile_images",
        "influencer_profile__cover_images",
        "followers",
        "following",
    )
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
