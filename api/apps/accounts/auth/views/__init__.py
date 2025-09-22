from apps.accounts.auth.views.login import LoginView
from apps.accounts.auth.views.register import RegisterView
from apps.accounts.auth.views.validate_email import ValidateEmailView
from apps.accounts.auth.views.resend_verification_code import ResendVerificationCodeView
from apps.accounts.auth.views.refresh import RefreshTokenView
from apps.accounts.auth.views.logout import LogoutView
from apps.accounts.auth.views.forgot_password import ForgotPasswordView
from apps.accounts.auth.views.reset_password import ResetPasswordView
from apps.accounts.auth.views.change_password import ChangePasswordView
# OTP views temporarily disabled due to import issues
# from apps.accounts.auth.views.login_otp import RequestOTPView, VerifyOTPView
# from apps.accounts.auth.views.forgot_password_otp import ForgotPasswordOTPView
# from apps.accounts.auth.views.reset_password_otp import ResetPasswordOTPView
# from apps.accounts.auth.views.is_valid_otp import IsValidOTPView
# from apps.accounts.auth.views.verify_registration_otp import VerifyRegistrationOTPView
# from apps.accounts.auth.views.send_email_otp import SendEmailOTPView


__all__ = [
    "LoginView",
    "RegisterView",
    "ValidateEmailView",
    "ResendVerificationCodeView",
    "RefreshTokenView",
    "LogoutView",
    "ForgotPasswordView",
    "ResetPasswordView",
    "ChangePasswordView",
    # OTP views temporarily disabled
    # "RequestOTPView",
    # "VerifyOTPView",
    # "ForgotPasswordOTPView",
    # "ResetPasswordOTPView",
    # "IsValidOTPView",
    # "VerifyRegistrationOTPView",
    # "SendEmailOTPView",
]
