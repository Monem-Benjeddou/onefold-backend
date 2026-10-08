from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .services import session_is_active


class SessionJWTAuthentication(JWTAuthentication):
    """JWT authentication that also refuses tokens from a revoked device session."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        sid = validated_token.get("sid")
        if sid and not session_is_active(sid, user.pk):
            raise AuthenticationFailed("This device was signed out.", code="session_revoked")
        return user
