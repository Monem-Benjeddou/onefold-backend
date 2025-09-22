from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _
import logging

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.serializers import UserSerializer
from apps.accounts.user.models import User
from apps.accounts.user.permissions import IsBusinessAdminOrNeoAdmin

logger = logging.getLogger(__name__)


@extend_schema(tags=["Admin"])
class DeleteUserView(DestroyAPIView):
    """
    View for deleting a user.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsBusinessAdminOrNeoAdmin]
    queryset = User.objects.all()
    lookup_field = "pk"

    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=60)
    @extend_schema(
        description="Delete a user",
        responses={
            204: _("No Content"),
            404: _("Not Found"),
            500: _("Internal Server Error"),
        },
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a user.
        """
        try:
            user_id = self.kwargs["pk"]
            logger.info(f"Starting deletion of user {user_id}")

            user = self.get_object()
            user.delete()

            logger.info(f"User {user_id} successfully deleted")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            logger.warning(f"User {self.kwargs.get('pk')} not found for deletion")
            return Response(
                {"error": _("User not found.")}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(
                f"Error deleting user {self.kwargs.get('pk')}: {str(e)}", exc_info=True
            )
            return Response(
                {"error": _("Error deleting user. Please try again later.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
