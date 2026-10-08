from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.demo import DEMO_DOMAIN, DEMO_STAGES, demo_email

from . import oauth, services
from .models import Session, SignInEvent, User
from .serializers import (
    ChangePasswordSerializer,
    DemoSignInSerializer,
    EmailSerializer,
    LoginSerializer,
    LogoutSerializer,
    OAuthCallbackSerializer,
    OAuthStartSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    SessionSerializer,
    SignInSerializer,
    TokenSerializer,
    UserSerializer,
)
from .services import Client

QUIET = {"detail": "If that address has an account, an email is on its way."}


class AuthFailed(APIException):
    """An AuthError as an API error: ``detail``, ``code``, ``request_id``, ``Retry-After``."""

    def __init__(self, error):
        self.status_code = error.status
        if error.retry_after:
            self.wait = error.retry_after
        super().__init__(detail=str(error), code=error.code)


def field_error(request, field, messages, code, status_code=400):
    return Response(
        {field: list(messages), "code": code, "request_id": request_id(request)},
        status=status_code,
    )


def weak_password(request, error, field="password"):
    return field_error(request, field, error.messages, "weak_password")


def request_id(request):
    return getattr(request._request, "request_id", None)


def signed_in(request, user, method, created=False):
    _, access, refresh = services.start_session(user, Client.from_request(request), method)
    return Response(
        {
            "access": access,
            "refresh": refresh,
            "created": created,
            "user": UserSerializer(user).data,
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


def current_sid(request):
    token = getattr(request, "auth", None)
    return str(token.get("sid")) if token is not None and token.get("sid") else None


class PublicView(APIView):
    """No authentication, throttled per client IP."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


# --- Configuration -------------------------------------------------------------


class AuthConfigView(PublicView):
    """Which sign-in methods the web app should offer."""

    throttle_classes = []

    @extend_schema(
        responses=inline_serializer(
            "AuthConfig",
            {
                "password": serializers.BooleanField(),
                "magic_link": serializers.BooleanField(),
                "providers": serializers.ListField(child=serializers.CharField()),
                "demo": serializers.BooleanField(),
                "dev_inbox_url": serializers.CharField(),
                "password_min_length": serializers.IntegerField(),
            },
        )
    )
    def get(self, request):
        return Response(
            {
                "password": True,
                "magic_link": True,
                "providers": oauth.enabled_providers(),
                "demo": settings.DEMO_LOGIN,
                "dev_inbox_url": settings.DEV_MAIL_INBOX_URL,
                "password_min_length": 10,
            }
        )


# --- Password ------------------------------------------------------------------


class LoginView(PublicView):
    @extend_schema(request=LoginSerializer, responses=SignInSerializer)
    def post(self, request):
        payload = LoginSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            user = services.authenticate_password(
                payload.validated_data["email"],
                payload.validated_data["password"],
                Client.from_request(request),
                request=request._request,
            )
        except services.AuthError as error:
            raise AuthFailed(error) from error
        return signed_in(request, user, "password")


class RegisterView(PublicView):
    @extend_schema(request=RegisterSerializer, responses={201: SignInSerializer})
    def post(self, request):
        payload = RegisterSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        try:
            user = services.register(
                data["email"], data["password"], data["name"], Client.from_request(request)
            )
        except services.EmailTaken as error:
            return field_error(request, "email", [str(error)], error.code, error.status)
        except DjangoValidationError as error:
            return weak_password(request, error)
        return signed_in(request, user, "password", created=True)


class ForgotPasswordView(PublicView):
    @extend_schema(request=EmailSerializer, responses={202: None})
    def post(self, request):
        payload = EmailSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        services.forgot_password(payload.validated_data["email"])
        return Response(QUIET, status=status.HTTP_202_ACCEPTED)


class ResetPasswordView(PublicView):
    @extend_schema(request=ResetPasswordSerializer, responses=SignInSerializer)
    def post(self, request):
        payload = ResetPasswordSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            user = services.reset_password(
                payload.validated_data["token"],
                payload.validated_data["password"],
                Client.from_request(request),
            )
        except services.AuthError as error:
            raise AuthFailed(error) from error
        except DjangoValidationError as error:
            return weak_password(request, error)
        return signed_in(request, user, "password_reset")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses={204: None})
    def post(self, request):
        payload = ChangePasswordSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            services.change_password(
                request.user,
                payload.validated_data["current_password"],
                payload.validated_data["new_password"],
                Client.from_request(request),
                keep_session=current_sid(request),
            )
        except services.AuthError as error:
            raise AuthFailed(error) from error
        except DjangoValidationError as error:
            return weak_password(request, error, "new_password")
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Email links -----------------------------------------------------------------


class MagicLinkRequestView(PublicView):
    @extend_schema(request=EmailSerializer, responses={202: None})
    def post(self, request):
        payload = EmailSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        services.request_link(payload.validated_data["email"])
        # Same answer whether or not the account exists, or the request was throttled.
        return Response(
            {"detail": "If that address can sign in, a link is on its way."},
            status=status.HTTP_202_ACCEPTED,
        )


class MagicLinkVerifyView(PublicView):
    @extend_schema(request=TokenSerializer, responses=SignInSerializer)
    def post(self, request):
        payload = TokenSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            user, created = services.redeem_link(payload.validated_data["token"])
        except services.AuthError as error:
            raise AuthFailed(error) from error
        response = signed_in(request, user, "magic_link", created=created)
        response.status_code = status.HTTP_200_OK
        return response


class VerifyEmailView(PublicView):
    @extend_schema(
        request=TokenSerializer,
        responses=inline_serializer("EmailVerified", {"email": serializers.EmailField()}),
    )
    def post(self, request):
        payload = TokenSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            user = services.verify_email(
                payload.validated_data["token"], Client.from_request(request)
            )
        except services.AuthError as error:
            raise AuthFailed(error) from error
        return Response({"email": user.email})


class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(request=None, responses={202: None})
    def post(self, request):
        if request.user.email_verified:
            return Response({"detail": "Your email is already confirmed."})
        services.send_verification(request.user)
        return Response(
            {"detail": f"We sent a new link to {request.user.email}."},
            status=status.HTTP_202_ACCEPTED,
        )


# --- Sessions --------------------------------------------------------------------


class LogoutView(APIView):
    """Sign this device out: revoke its session and blacklist the refresh token."""

    permission_classes = [AllowAny]
    # Identified by the refresh token alone: an expired access token must not
    # stop anyone from signing out.
    authentication_classes = []

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        payload = LogoutSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        sid, user_id = None, None
        if payload.validated_data["refresh"]:
            try:
                refresh = RefreshToken(payload.validated_data["refresh"])
                sid = refresh.get("sid")
                user_id = refresh.get("user_id")
                refresh.blacklist()
            except TokenError:
                pass  # already expired or revoked: signing out still succeeds
        session = Session.objects.filter(pk=sid).select_related("user").first() if sid else None
        if session:
            services.revoke_session(session)
            services.record(
                SignInEvent.Kind.SIGNED_OUT, Client.from_request(request), user=session.user
            )
        elif user_id:
            user = User.objects.filter(pk=user_id).first()
            if user:
                services.record(
                    SignInEvent.Kind.SIGNED_OUT, Client.from_request(request), user=user
                )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionListView(generics.ListAPIView):
    """The builder's signed-in devices."""

    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Session.objects.none()
        return Session.objects.filter(user=self.request.user, revoked_at__isnull=True)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "current_sid": current_sid(self.request)}


class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, pk):
        session = Session.objects.filter(pk=pk, user=request.user).first()
        if session is None:
            raise Http404
        services.revoke_session(session, Client.from_request(request))
        return Response(status=status.HTTP_204_NO_CONTENT)


class RevokeOtherSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses=inline_serializer("Revoked", {"revoked": serializers.IntegerField()}),
    )
    def post(self, request):
        count = services.revoke_all_sessions(request.user, keep=current_sid(request))
        if count:
            services.record(
                SignInEvent.Kind.SESSION_REVOKED, Client.from_request(request), user=request.user
            )
        return Response({"revoked": count})


# --- GitHub / Google ------------------------------------------------------------


class OAuthStartView(PublicView):
    @extend_schema(
        request=OAuthStartSerializer,
        responses=inline_serializer(
            "OAuthStart",
            {"authorize_url": serializers.URLField(), "state": serializers.CharField()},
        ),
    )
    def post(self, request, provider):
        payload = OAuthStartSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            url, state = oauth.authorize_url(provider, payload.validated_data["next"])
        except oauth.OAuthError as error:
            raise AuthFailed(error) from error
        return Response({"authorize_url": url, "state": state})


class OAuthCallbackView(PublicView):
    @extend_schema(
        request=OAuthCallbackSerializer,
        responses=inline_serializer(
            "OAuthSignIn",
            {
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
                "created": serializers.BooleanField(),
                "next": serializers.CharField(),
                "user": UserSerializer(),
            },
        ),
    )
    def post(self, request, provider):
        payload = OAuthCallbackSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            user, created, next_path = oauth.complete(
                provider, payload.validated_data["code"], payload.validated_data["state"]
            )
        except oauth.OAuthError as error:
            raise AuthFailed(error) from error
        response = signed_in(request, user, provider, created=created)
        response.data["next"] = next_path
        response.status_code = status.HTTP_200_OK
        return response


# --- Development: one-click demo accounts ---------------------------------------


class DemoSignInView(PublicView):
    """Sign in as a seeded demo account. 404 unless DEBUG and DEMO_LOGIN are on."""

    throttle_classes = []

    def initial(self, request, *args, **kwargs):
        if not settings.DEMO_LOGIN:
            raise Http404
        super().initial(request, *args, **kwargs)

    @extend_schema(
        responses=inline_serializer(
            "DemoAccount",
            {
                "email": serializers.EmailField(),
                "name": serializers.CharField(),
                "stage": serializers.CharField(),
            },
            many=True,
        )
    )
    def get(self, request):
        users = {
            u.email: u
            for u in User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}", is_active=True)
        }
        return Response(
            [
                {
                    "email": demo_email(handle),
                    "name": users[demo_email(handle)].name,
                    "stage": stage,
                }
                for handle, stage in DEMO_STAGES.items()
                if demo_email(handle) in users
            ]
        )

    @extend_schema(request=DemoSignInSerializer, responses=SignInSerializer)
    def post(self, request):
        payload = DemoSignInSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        email = payload.validated_data["email"].lower()
        user = User.objects.filter(email=email, is_active=True, is_staff=False).first()
        if user is None or not email.endswith(f"@{DEMO_DOMAIN}"):
            raise Http404
        return signed_in(request, user, "demo")


# --- The signed-in builder --------------------------------------------------------


class MeView(generics.RetrieveUpdateDestroyAPIView):
    """The signed-in builder. DELETE removes the account and all its data."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_object(self):
        return self.request.user
