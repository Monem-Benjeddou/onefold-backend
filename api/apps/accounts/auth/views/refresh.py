from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.exceptions import APIException
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.exceptions import TokenError

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit


class ValidationError400(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Invalid input.")
    default_code = "invalid"


class RefreshTokenView(TokenRefreshView):
    """
    API View for refreshing access tokens.
    """

    permission_classes = (AllowAny,)

    @api_error_handler
    @dynamic_rate_limit(default_rate=20, default_period=300)
    @extend_schema(
        tags=["auth"],
        responses={
            200: {"description": _("Token refresh successful.")},
            401: {"description": _("Token is invalid or expired")},
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Refresh an access token using a valid refresh token.
        Returns a new access token.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise ValidationError400(_("Token is invalid or expired"))

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
