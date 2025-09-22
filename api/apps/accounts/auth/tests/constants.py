from django.urls import reverse

REGISTER_URL = reverse("auth-register")
VALIDATE_EMAIL_URL = reverse("auth-validate-email")
LOGIN_URL = reverse("auth-login")
REFRESH_URL = reverse("auth-refresh")
LOGOUT_URL = reverse("auth-logout")
FORGOT_PASSWORD_URL = reverse("auth-forgot-password")
RESET_PASSWORD_URL = reverse("auth-reset-password")
RESEND_VERIFICATION_CODE_URL = reverse("auth-resend-verification-code")
USER_CREDENTIALS = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "testpassword",
}
USER_PHONE = "+21626726826"
LOGIN_OTP_URL = "auth-login-otp"
VERIFY_OTP_URL = "auth-verify-otp"
USER_EMAIL = "test@example.com"
INVALID_EMAIL = "invalid@example.com"
PASSWORD = "testpassword123"
INVALID_PASSWORD = "short"
TOKEN = "valid-token"
INVALID_TOKEN = "invalid-token"
CODE = "123456"
INVALID_CODE = "000000"
