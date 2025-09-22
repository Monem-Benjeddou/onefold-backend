from django.db import models
from django.utils import timezone
from django.conf import settings

EXPIRATION = getattr(settings, "OTP_EXPIRATION_MINS", 10)


def default_expiration():
    return timezone.now() + timezone.timedelta(minutes=EXPIRATION)


OTP_PURPOSE_CHOICES = [
    ("login", "Login"),
    ("registration", "Registration"),
    ("password_reset", "Password Reset"),
    ("verification", "Verification"),
]

OTP_DELIVERY_METHOD_CHOICES = [
    ("email", "Email"),
    ("sms", "SMS"),
    ("fallback", "SMS with Email Fallback"),
]


class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="otps", on_delete=models.CASCADE)
    code = models.CharField(max_length=6, help_text="6-digit numeric OTP code")
    purpose = models.CharField(
        max_length=20, choices=OTP_PURPOSE_CHOICES, default="login"
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=OTP_DELIVERY_METHOD_CHOICES,
        default="email",
        help_text="Method used to deliver the OTP",
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiration)

    class Meta:
        indexes = [
            models.Index(fields=["user", "purpose", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_valid(self):
        """Check if the OTP is valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark the OTP as used."""
        self.is_used = True
        self.save(update_fields=["is_used"])

    def __str__(self):
        return f"{self.user.email} - {self.code} ({self.purpose})"
