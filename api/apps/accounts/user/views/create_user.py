from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.serializers import CreateUserSerializer
from apps.accounts.user.permissions import IsBusinessAdminOrNeoAdmin


@extend_schema(tags=["Admin"])
class CreateUserView(CreateAPIView):
    """
    View for creating a new user.
    """

    serializer_class = CreateUserSerializer
    permission_classes = [IsAuthenticated, IsBusinessAdminOrNeoAdmin]

    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=60)
    @extend_schema(
        description="""
        Create a new user with specified role.
        
        If no role is provided, 'user' will be assigned by default.
        
        Available roles:
        - user: Regular user
        - admin: Administrator with elevated privileges
        - moderator: Platform moderator
        - influencer: Content creator
        - service: Service provider
        - manufacturer: Manufacturer
        - collector: Collector
        - issuer: Card/NFT issuer
        """,
        request=CreateUserSerializer,
        responses={201: CreateUserSerializer, 400: _("Bad Request")},
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new user with the provided data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if not user.role:
            user.role = "user"
            user.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
