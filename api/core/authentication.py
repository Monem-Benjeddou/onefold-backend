"""
Custom Authentication Classes

This module provides custom authentication classes with enhanced error handling
for JWT authentication issues, particularly around user existence validation.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication with enhanced error handling.

    This class provides better error messages and handling for common JWT
    authentication issues, particularly when users are deleted but tokens
    are still valid.
    """

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.

        Provides enhanced error handling for cases where the user referenced
        in the token no longer exists in the database.
        """
        try:
            user_id = validated_token[self.get_user_id_claim()]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = User.objects.get(**{self.get_user_id_field(): user_id})
        except User.DoesNotExist:
            raise AuthenticationFailed(
                {
                    "detail": "User not found",
                    "code": "user_not_found",
                    "user_id": str(user_id),
                    "help": "The user referenced by this token no longer exists. Please log in again.",
                }
            )
        except Exception:

            raise AuthenticationFailed(
                {
                    "detail": "Authentication error",
                    "code": "auth_error",
                    "help": "An unexpected authentication error occurred. Please try again.",
                }
            )

        if not user.is_active:
            raise AuthenticationFailed(
                {
                    "detail": "User account is disabled",
                    "code": "user_inactive",
                    "help": "Your account has been deactivated. Please contact support.",
                }
            )

        try:
            if hasattr(user, "is_currently_banned") and user.is_currently_banned():
                ban_message = "Your account has been temporarily banned."
                if hasattr(user, "ban_reason") and user.ban_reason:
                    ban_message += f" Reason: {user.ban_reason}"
                if hasattr(user, "ban_expires_at") and user.ban_expires_at:
                    ban_message += f" Ban expires at: {user.ban_expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                else:
                    ban_message += " This is a permanent ban."

                raise AuthenticationFailed(
                    {
                        "detail": ban_message,
                        "code": "user_banned",
                        "help": "Please contact support if you believe this is an error.",
                    }
                )
        except AttributeError:

            pass

        return user

    def get_user_id_claim(self):
        """Get the user ID claim from JWT settings"""
        from django.conf import settings

        return getattr(settings, "SIMPLE_JWT", {}).get("USER_ID_CLAIM", "user_id")

    def get_user_id_field(self):
        """Get the user ID field from JWT settings"""
        from django.conf import settings

        return getattr(settings, "SIMPLE_JWT", {}).get("USER_ID_FIELD", "id")

    def authenticate(self, request):
        """
        Authenticate the request with enhanced error handling.
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except TokenError as e:

            if "User not found" in str(e):
                raise AuthenticationFailed(
                    {
                        "detail": "User not found",
                        "code": "user_not_found",
                        "help": "Please log in again to refresh your authentication.",
                    }
                )
            raise AuthenticationFailed(
                {
                    "detail": "Invalid token",
                    "code": "invalid_token",
                    "help": "Your authentication token is invalid. Please log in again.",
                }
            )
        except AuthenticationFailed:

            raise
        except Exception as e:

            raise AuthenticationFailed(
                {
                    "detail": "Authentication error",
                    "code": "auth_error",
                    "help": "An unexpected authentication error occurred. Please try again.",
                }
            )
