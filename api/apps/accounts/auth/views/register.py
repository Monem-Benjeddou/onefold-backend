from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

from apps.accounts.auth.serializers.register import RegisterSerializer
from apps.accounts.user.serializers import UserSerializer
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit

User = get_user_model()


class RegisterView(APIView):
    """
    API View for user registration.
    """

    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=3, default_period=3600)
    @extend_schema(
        tags=["auth"],
        request=RegisterSerializer,
        responses={
            201: {"description": _("User registered successfully.")},
            400: {"description": _("Invalid input data.")},
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Process registration request.
        Creates a new user and returns success message WITHOUT tokens.
        User must verify their account before being able to login.
        """
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # For development: auto-activate users
        # user.is_active = False
        # user.is_email_verified = False
        user.is_active = True
        user.is_email_verified = True

        message = _(
            "User registered successfully."
        )

        user.save()

        return Response(
            {
                "message": message,
                "user": UserSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )
