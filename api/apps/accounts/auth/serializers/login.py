from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext as _
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from apps.accounts.user.serializers import UserSerializer
from apps.accounts.user.models import User


class LoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def get_user(self, email):
        """Retrieve user by email or phone number."""

        email = email.lower() if email else None

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            raise AuthenticationFailed(
                _("User does not exist."),
                code=status.HTTP_404_NOT_FOUND,
            )
        return user

    def validate(self, attrs):
        user = self.get_user(attrs.get("email"))
        if not user.check_password(attrs.get("password")):
            raise AuthenticationFailed(
                _("Invalid credentials."), code=status.HTTP_401_UNAUTHORIZED
            )


        if hasattr(user, "is_currently_banned") and user.is_currently_banned():
            ban_message = _("Your account has been temporarily banned.")
            if user.ban_reason:
                ban_message += f" Reason: {user.ban_reason}"
            if user.ban_expires_at:
                ban_message += f" Ban expires at: {user.ban_expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            else:
                ban_message += _(" This is a permanent ban.")

            raise PermissionDenied(ban_message)

        request = self.context.get("request")
        only_admins = False

        if request and hasattr(request, "query_params"):
            only_admins = (
                request.query_params.get("only_admins", "false").lower() == "true"
            )
        elif request and hasattr(request, "GET"):
            only_admins = request.GET.get("only_admins", "false").lower() == "true"

        if only_admins and not user.is_staff:
            raise AuthenticationFailed(
                _("Only admin users are allowed to log in."),
                code=status.HTTP_403_FORBIDDEN,
            )

        refresh = self.get_token(user)
        data = {
            "user": UserSerializer(user, context=self.context).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return data
