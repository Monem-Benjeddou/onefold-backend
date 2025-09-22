import os
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from django.template.exceptions import TemplateDoesNotExist
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from config.settings.config_loader import get_frontend_config
from apps.accounts.auth.serializers import ChangePasswordSerializer

User = get_user_model()

frontend_config = get_frontend_config()
UI_BASE_URL = frontend_config["UI_URLS"]["CANDIDATE"] or frontend_config["URL"]
logger = logging.getLogger(__name__)


class ChangePasswordView(APIView):
    """
    API View for changing a logged-in user's password.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=300)
    @extend_schema(
        tags=["auth"],
        request=ChangePasswordSerializer,
        responses={200: {"description": "Password has been changed successfully."}},
    )
    def post(self, request, *args, **kwargs):
        """
        Process password change request.
        Validates current password and sets a new one.
        """
        try:
            serializer = self.serializer_class(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"message": _("Password has been changed successfully.")},
                status=status.HTTP_200_OK,
            )
        except TemplateDoesNotExist as e:
            logger.error(e)
            return Response(
                {"error": _("Email template does not exist.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
