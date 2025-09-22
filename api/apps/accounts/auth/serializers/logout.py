from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        help_text=_("The refresh token to be blacklisted"),
        error_messages={
            "required": _("A refresh token is required."),
            "blank": _("A refresh token is required."),
        },
    )
