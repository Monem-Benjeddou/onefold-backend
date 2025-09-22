from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.accounts.auth.serializers.login import LoginSerializer
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit


class LoginView(APIView):
    """
    API View for user login. Returns tokens upon successful authentication.
    """

    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    @dynamic_rate_limit(default_rate=5, default_period=60)
    @api_error_handler
    @extend_schema(
        tags=["auth"],
        request=LoginSerializer,
        responses={200: {"description": _("Login successful.")}},
        parameters=[
            OpenApiParameter(
                name="only_admins",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Only allow admin users to login. If set to true, non-admin users will be blocked.",
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        """
        Process login request.
        Returns user data and auth tokens.
        """
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
