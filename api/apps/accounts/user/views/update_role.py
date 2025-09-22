from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.models import User
from apps.accounts.user.constants import ROLE_CHOICES
from apps.accounts.user.permissions import IsBusinessAdminOrNeoAdmin


@extend_schema(tags=["Admin"])
class UpdateRoleView(APIView):
    """
    View for updating a user's role.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdminOrNeoAdmin]

    def get_object(self, pk):
        """
        Get the user object by primary key.
        """
        try:
            obj = User.objects.get(pk=pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except User.DoesNotExist:
            return None

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    @extend_schema(
        description="""
        Update user role to a new role.
        
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
        request={"application/json": {"example": {"role": "admin"}}},
        responses={
            200: {
                "description": "Role updated successfully",
                "content": {
                    "application/json": {"example": {"status": "Role updated to admin"}}
                },
            },
            400: {
                "description": "Invalid role provided",
                "content": {"application/json": {"example": {"error": "Invalid role"}}},
            },
            404: _("Not Found"),
        },
    )
    def patch(self, request, pk=None):
        """
        Update a user's role.
        """
        user = self.get_object(pk)
        if not user:
            return Response(
                {"error": _("User not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        new_role = request.data.get("role")
        if new_role in dict(ROLE_CHOICES):
            user.role = new_role
            user.save()
            return Response(
                {"status": f"Role updated to {new_role}"}, status=status.HTTP_200_OK
            )
        return Response(
            {"error": _("Invalid role")}, status=status.HTTP_400_BAD_REQUEST
        )
