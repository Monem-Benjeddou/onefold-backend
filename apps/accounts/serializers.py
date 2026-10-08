from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .models import Session, SocialAccount, User


class UserSerializer(serializers.ModelSerializer):
    email_verified = serializers.BooleanField(read_only=True)
    has_password = serializers.SerializerMethodField()
    onboarding_complete = serializers.SerializerMethodField()
    connected = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "created",
            "email_verified",
            "has_password",
            "onboarding_complete",
            "connected",
        ]
        read_only_fields = ["id", "email", "created"]

    @extend_schema_field(serializers.BooleanField())
    def get_has_password(self, obj):
        return obj.has_usable_password()

    @extend_schema_field(serializers.BooleanField())
    def get_onboarding_complete(self, obj):
        from apps.workspace.services import is_onboarded

        return is_onboarded(obj)

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_connected(self, obj):
        return [account.provider for account in obj.social_accounts.all()]


class SignInSerializer(serializers.Serializer):
    """Every successful sign-in answers with this."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    created = serializers.BooleanField()
    user = UserSerializer()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)


# Kept for the magic-link endpoints' schema names.
MagicLinkRequestSerializer = EmailSerializer
MagicLinkVerifySerializer = TokenSerializer


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=256, trim_whitespace=False)


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    email = serializers.EmailField()
    password = serializers.CharField(max_length=256, trim_whitespace=False)


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(max_length=256, trim_whitespace=False)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=256, trim_whitespace=False, required=False, allow_blank=True, default=""
    )
    new_password = serializers.CharField(max_length=256, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True, default="")


class OAuthStartSerializer(serializers.Serializer):
    next = serializers.CharField(required=False, allow_blank=True, default="", max_length=300)


class OAuthCallbackSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=2000)
    state = serializers.CharField(max_length=2000)


class DemoSignInSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SessionSerializer(serializers.ModelSerializer):
    current = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = ["id", "method", "user_agent", "ip", "created", "last_seen_at", "current"]

    @extend_schema_field(serializers.BooleanField())
    def get_current(self, obj):
        return str(obj.id) == self.context.get("current_sid")


class SocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        fields = ["provider", "login", "created"]


class SessionTokenRefreshSerializer(TokenRefreshSerializer):
    """Refresh, unless the device session was revoked; marks the device as seen."""

    def validate(self, attrs):
        sid = self.token_class(attrs["refresh"]).get("sid")
        if sid:
            alive = Session.objects.filter(pk=sid, revoked_at__isnull=True).update(
                last_seen_at=timezone.now()
            )
            if not alive:
                raise InvalidToken("This device was signed out.")
        return super().validate(attrs)
