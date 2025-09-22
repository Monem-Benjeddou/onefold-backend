import os
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from core.tasks import send_activation_email
from apps.accounts.user.models import UserToken

User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError(_("Invalid old password"))
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(_("Passwords do not match"))
        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        text_content = _("Your password has been changed successfully")
        html_content = render_to_string("change_password_email.html")
        send_activation_email(
            _("Password Changed"),
            text_content,
            user.email,
            html_content=html_content,
        )
