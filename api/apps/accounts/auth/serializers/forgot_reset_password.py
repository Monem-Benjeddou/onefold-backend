from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework import serializers
from rest_framework.exceptions import APIException
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import NotFound

from core.tasks import send_activation_email
from apps.accounts.user.models import UserToken

User = get_user_model()


class ValidationError400(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid input.")
    default_code = "invalid"


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(style={"input_type": "password"}, required=True)
    token = serializers.CharField(required=True)

    def validate(self, data):
        token = data["token"]
        if not UserToken.objects.filter(token=token).exists():
            raise ValidationError400(_("Invalid or expired token"))
        user = UserToken.objects.get(token=token).user
        if not PasswordResetTokenGenerator().check_token(user, data["token"]):
            raise ValidationError400(_("Invalid or expired token"))
        if user.check_password(data["password"]):
            raise serializers.ValidationError(
                {"password": _("You can't use the old password")}
            )
        return data

    def save(self, **kwargs):
        user = UserToken.objects.get(token=self.validated_data["token"]).user
        user.set_password(self.validated_data["password"])
        user.save()
        UserToken.objects.get(token=self.validated_data["token"]).delete()
        text_content = _("Your password has been reset successfully.")
        html_content = render_to_string("reset_password_confirmation_email.html")

        send_activation_email(
            _("Password Reset Confirmation"),
            text_content,
            user.email,
            html_content=html_content,
        )
