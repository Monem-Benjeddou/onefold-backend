from django.urls import path

from apps.accounts.auth.views import (
    LoginView,
    RegisterView,
    RefreshTokenView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    # OTP endpoints temporarily disabled
    # path("login-otp/", RequestOTPView.as_view(), name="auth-login-otp"),
    # path("verify-otp/", VerifyOTPView.as_view(), name="auth-verify-otp"),
    # path(
    #     "forgot-password-otp/",
    #     ForgotPasswordOTPView.as_view(),
    #     name="auth-forgot-password-otp",
    # ),
    # path(
    #     "reset-password-otp/",
    #     ResetPasswordOTPView.as_view(),
    #     name="auth-reset-password-otp",
    # ),
    # path("is-valid-otp/", IsValidOTPView.as_view(), name="auth-is-valid-otp"),
    # path(
    #     "verify-registration-otp/",
    #     VerifyRegistrationOTPView.as_view(),
    #     name="auth-verify-registration-otp",
    # ),
    # path("send-email-otp/", SendEmailOTPView.as_view(), name="auth-send-email-otp"),
]
