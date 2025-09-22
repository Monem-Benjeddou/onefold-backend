import os
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
import logging

from core.tasks import send_activation_email
from apps.accounts.user.models import UserToken
from core.tasks.sms import send_sms_task

User = get_user_model()
logger = logging.getLogger(__name__)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    testing = serializers.BooleanField(required=False, default=False)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("User does not exist."))
        return value

    def get_forgot_password_link(self):
        """
        Returns the forgot password link from environment variables.
        Falls back to localhost if not configured.
        """
        forgot_password_link = os.environ.get("FORGOT_PASSWORD_LINK")
        if not forgot_password_link:
            logger.warning(
                "FORGOT_PASSWORD_LINK not configured, using localhost fallback"
            )
            forgot_password_link = "http://localhost:5173/auth/reset-password"
        return forgot_password_link

    def save(self, **kwargs):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)

        token = PasswordResetTokenGenerator().make_token(user)

        forgot_password_base = self.get_forgot_password_link()
        reset_link = f"{forgot_password_base}?token={token}"

        UserToken.objects.get_or_create(user=user, token=token)
        text_content = _(
            f"Click the link below to reset your password:\n{reset_link}\n\nReset Token: {token}"
        )
        html_content = render_to_string(
            "forgot_password_email.html", {"reset_url": reset_link, "token": token}
        )
        if "@" in email:

            try:
                email_sent = send_activation_email(
                    _("Password Reset Request"),
                    text_content,
                    email,
                    html_content=html_content,
                )
                if not email_sent:
                    logger.warning(f"Password reset email failed to send to {email}")
            except Exception as e:

                logger.error(
                    f"Unexpected error sending password reset email to {email}: {str(e)}"
                )
        else:
            try:
                send_sms_task.delay(text_content, [email])
            except Exception as e:
                logger.error(f"Failed to send password reset SMS to {email}: {str(e)}")
