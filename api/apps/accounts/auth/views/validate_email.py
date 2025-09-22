from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema

from apps.accounts.auth.serializers import EmailVerificationSerializer
from apps.accounts.user.models import VerificationCode
from apps.accounts.user.serializers import UserSerializer
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit


class ValidateEmailView(APIView):
    """
    API View for validating email verification codes.
    """

    serializer_class = EmailVerificationSerializer

    @extend_schema(
        tags=["auth"],
        request=EmailVerificationSerializer,
        responses={200: UserSerializer},
    )
    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=300)
    def post(self, request):
        """
        Validates the verification code (OTP or legacy) and activates the user account.
        Returns user data and tokens upon successful verification.
        Supports both new OTP system and legacy VerificationCode for backward compatibility.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data.get("user")
            verification_type = serializer.validated_data.get("verification_type")

            if verification_type == "otp":
                
                otp = serializer.validated_data.get("otp")

                try:
                    from django.db import transaction

                    
                    verification_updates = {
                        "is_active": True,
                        "is_email_verified": True,
                        "is_phone_verified": True,
                        "is_verified": True,
                    }

                    with transaction.atomic():
                        
                        otp.mark_as_used()

                        
                        for field, value in verification_updates.items():
                            setattr(user, field, value)

                        update_fields = list(verification_updates.keys()) + ["updated"]
                        user.save(update_fields=update_fields)

                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"User {user.email} account verified via email OTP. Updated fields: {list(verification_updates.keys())}"
                    )

                except Exception as e:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"Failed to verify account via OTP for {user.email}: {str(e)}"
                    )
                    return Response(
                        {
                            "error": {
                                "code": _("Verification failed. Please try again.")
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            else:
                
                verification_code = serializer.validated_data.get("verification_code")

                
                user.is_active = True
                user.is_email_verified = True
                user.is_phone_verified = True
                user.is_verified = True
                user.save(
                    update_fields=[
                        "is_active",
                        "is_email_verified",
                        "is_phone_verified",
                        "is_verified",
                        "updated",
                    ]
                )

                verification_code.delete()

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": _("Account verified successfully"),
                    "user": UserSerializer(user, context={"request": request}).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
