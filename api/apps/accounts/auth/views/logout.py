from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema

from apps.accounts.auth.serializers.logout import LogoutSerializer
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit


class LogoutView(APIView):
    """
    API View for user logout. Blacklists the refresh token.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = LogoutSerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=300)
    @extend_schema(
        tags=["auth"],
        request=LogoutSerializer,
        responses={204: {"description": "Logout successful."}},
    )
    def post(self, request, *args, **kwargs):
        """
        Process logout request.
        Blacklists the refresh token to prevent its future use.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get("refresh")

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TokenError:
            raise ValidationError({"error": _("The refresh token is invalid.")})
