from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.serializers.create_issuer import CreateIssuerSerializer
from apps.accounts.user.permissions import IsCardCreatorOrAdminOrSalesman


@extend_schema(tags=["Admin", "Card creation"])
class CreateIssuerAPIView(CreateAPIView):
    """
    API view for creating issuer users.
    Only card creators, admins, salesman, and superusers can create issuers.
    """

    serializer_class = CreateIssuerSerializer
    permission_classes = [IsAuthenticated, IsCardCreatorOrAdminOrSalesman]

    @api_error_handler
    @dynamic_rate_limit(default_rate=3, default_period=60)
    @extend_schema(
        description="""
        Create a new issuer user.
        
        Only card creators, admins, salesman, and superusers can create issuers. 
        The role will be automatically set to 'issuer' during creation.
        
        Required fields:
        - email: Must be unique
        - fullname: Full name of the issuer
        - phone_number: Must be in E.164 format (e.g., +1234567890)
        
        Optional fields:
        - country: Country where the issuer operates
        - avatar: Profile image
        - website: Issuer's website URL
        - vat_number: VAT/tax identification number
        """,
        request=CreateIssuerSerializer,
        responses={
            201: CreateIssuerSerializer,
            400: _("Bad Request - Validation errors"),
            403: _("Forbidden - Card creator, admin, or salesman access required"),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new issuer user with the provided data.

        The user's role will automatically be set to 'issuer'.
        Only card creators, admins, salesman, and superusers can perform this action.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        issuer = serializer.save()

        response_data = serializer.data
        response_data["message"] = _("Issuer created successfully.")

        return Response(response_data, status=status.HTTP_201_CREATED)
