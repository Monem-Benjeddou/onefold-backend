import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes

from core.decorators.error_handler import api_error_handler
from apps.accounts.auth.serializers.forgot_password_serializer import (
    ForgotPasswordSerializer,
)
from core.ratelimiter import dynamic_rate_limit

User = get_user_model()


class ForgotPasswordView(APIView):
    """
    API View for requesting a password reset.
    """

    permission_classes = (AllowAny,)
    serializer_class = ForgotPasswordSerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=3600)
    @extend_schema(
        tags=["auth"],
        request=ForgotPasswordSerializer,
        responses={
            200: {"description": _("Password reset email sent successfully.")},
            400: {"description": _("Invalid input data.")},
            401: {"description": _("User does not exist.")},
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Process forgot password request.
        Sends a password reset email to the user.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": _("Password reset email sent.")},
            status=status.HTTP_200_OK,
        )
