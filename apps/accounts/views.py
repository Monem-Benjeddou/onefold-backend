from django.contrib.auth.models import update_last_login
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from . import services
from .serializers import MagicLinkRequestSerializer, MagicLinkVerifySerializer, UserSerializer


class MagicLinkRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=MagicLinkRequestSerializer, responses={202: None})
    def post(self, request):
        payload = MagicLinkRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        services.request_link(payload.validated_data["email"])
        # Same answer whether or not the account exists, or the request was throttled.
        return Response(
            {"detail": "If that address can sign in, a link is on its way."},
            status=status.HTTP_202_ACCEPTED,
        )


class MagicLinkVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=MagicLinkVerifySerializer,
        responses=inline_serializer(
            "SignIn",
            {
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
                "created": serializers.BooleanField(),
                "user": UserSerializer(),
            },
        ),
    )
    def post(self, request):
        payload = MagicLinkVerifySerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            user, created = services.redeem_link(payload.validated_data["token"])
        except services.InvalidLink as error:
            return Response(
                {"detail": str(error), "code": error.code}, status=status.HTTP_400_BAD_REQUEST
            )
        update_last_login(None, user)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "created": created,
                "user": UserSerializer(user).data,
            }
        )


class MeView(generics.RetrieveUpdateDestroyAPIView):
    """The signed-in builder. DELETE removes the account and all its data."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_object(self):
        return self.request.user
