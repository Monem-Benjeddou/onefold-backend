import logging
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

User = get_user_model()
logger = logging.getLogger(__name__)


class SendEmailOTPSerializer(serializers.Serializer):
    """
    Serializer for sending email OTP for account verification.
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validate that the email exists and corresponds to a registered user.
        """
        email = value.lower()
        try:
            user = User.objects.get(email__iexact=email)
            return email
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User with this email does not exist."))

    def validate(self, data):
        """
        Additional validation and add user to validated data.
        """
        email = data.get("email")
        try:
            user = User.objects.get(email__iexact=email)
            data["user"] = user

            
            if not user.email:
                raise serializers.ValidationError(
                    {"email": _("Email address is required for email OTP delivery.")}
                )

            return data
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": _("User with this email does not exist.")}
            )


class SendEmailOTPView(APIView):
    """
    API View for sending OTP via email for account verification.
    Uses the existing OTP model with purpose="verification" and delivery_method="email".
    """

    permission_classes = (AllowAny,)
    serializer_class = SendEmailOTPSerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=3, default_period=300)  
    @extend_schema(
        tags=["auth"],
        request=SendEmailOTPSerializer,
        responses={
            200: {"description": _("Email OTP sent successfully.")},
            400: {"description": _("Invalid email or user not found.")},
            429: {"description": _("Rate limit exceeded.")},
        },
        summary="Send Email OTP for Verification",
        description="""
        Send an OTP code via email for account verification.
        
        This endpoint:
        - Generates a new OTP with purpose="verification" and delivery_method="email"
        - Sends the OTP to the user's registered email address
        - Clears any existing verification OTPs for the user
        - Uses the existing OTPDeliveryService for email sending
        
        The OTP code can then be used with the validate-email endpoint to verify the account.
        """,
    )
    def post(self, request, *args, **kwargs):
        """
        Process email OTP request.
        Generates and sends OTP to the user's email for verification.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get("user")
        if not user:
            raise serializers.ValidationError(
                {"error": [_("User could not be found.")]}
            )

        
        if not hasattr(user, "generate_verification_code"):
            logger.error(
                f"User model missing generate_verification_code method. User: {user}"
            )
            raise serializers.ValidationError(
                {
                    "error": [
                        _("OTP functionality not available. Please contact support.")
                    ]
                }
            )

        
        if not user.email:
            raise serializers.ValidationError(
                {"email": [_("Email address is required for email OTP delivery.")]}
            )

        try:
            
            code = user.generate_verification_code(purpose="verification")
            logger.info(
                f"Generated email verification OTP for user {user.email}: {len(code)} characters"
            )
        except Exception as e:
            logger.error(
                f"Failed to generate email OTP for user {user.email}: {str(e)}"
            )
            raise serializers.ValidationError(
                {"error": [_("Failed to generate OTP. Please try again.")]}
            )

        try:
            
            otp_sent = OTPDeliveryService._send_otp_via_email(
                user, code, "verification"
            )
            if not otp_sent:
                logger.warning(f"Failed to send email OTP to user {user.email}")
                raise serializers.ValidationError(
                    {"error": [_("Failed to send email OTP. Please try again.")]}
                )
        except Exception as e:
            logger.error(f"Failed to send email OTP to user {user.email}: {str(e)}")
            raise serializers.ValidationError(
                {"error": [_("Failed to send email OTP. Please try again.")]}
            )

        
        email = user.email
        if "@" in email:
            username, domain = email.split("@", 1)
            if len(username) > 2:
                
                masked_username = username[:2] + "*" + username[-1:]
            else:
                masked_username = "*" * len(username)
            masked_email = f"{masked_username}@{domain}"
        else:
            masked_email = "*" * len(email)

        return Response(
            {
                "message": _("Email verification OTP sent to {}").format(masked_email),
                "email": masked_email,
            },
            status=status.HTTP_200_OK,
        )
