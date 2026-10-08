from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        if password:
            user.set_password(password)
        else:
            # Accounts made by a magic link or GitHub/Google have no password
            # until the builder sets one (Forgot password proves the inbox first).
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.update(is_staff=True, is_superuser=True)
        return self.create_user(email, password, **extra)


class User(TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # Set once the builder proves they own the inbox (verify link, magic link,
    # password reset, or a verified address from GitHub/Google).
    email_verified_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.email

    @property
    def email_verified(self):
        return self.email_verified_at is not None


class MagicLink(TimeStampedModel):
    """
    A single-use emailed token: a sign-in link, a password reset or an email
    confirmation. Only a hash of the token is stored.
    """

    class Purpose(models.TextChoices):
        SIGN_IN = "sign_in", "Sign in"
        PASSWORD_RESET = "password_reset", "Password reset"
        VERIFY_EMAIL = "verify_email", "Verify email"

    email = models.EmailField(db_index=True)
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.SIGN_IN)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.email} · {self.purpose} ({'used' if self.used_at else 'open'})"


class Session(TimeStampedModel):
    """
    One signed-in device. Its id travels in every JWT as the ``sid`` claim, so
    revoking it ends that device's session at its next request.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    method = models.CharField(max_length=20)
    user_agent = models.CharField(max_length=300, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.user_id} · {self.method} · {'revoked' if self.revoked_at else 'active'}"

    @property
    def is_active(self):
        return self.revoked_at is None


class SocialAccount(TimeStampedModel):
    """A GitHub or Google identity linked to a user."""

    class Provider(models.TextChoices):
        GITHUB = "github", "GitHub"
        GOOGLE = "google", "Google"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_accounts")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    uid = models.CharField(max_length=191)
    login = models.CharField(max_length=191, blank=True, help_text="Username or email there")

    class Meta:
        ordering = ["provider"]
        constraints = [
            models.UniqueConstraint(fields=["provider", "uid"], name="uniq_social_identity"),
            models.UniqueConstraint(fields=["user", "provider"], name="one_identity_per_provider"),
        ]

    def __str__(self):
        return f"{self.provider}:{self.login or self.uid}"


class SignInEvent(models.Model):
    """Append-only audit trail of authentication events."""

    class Kind(models.TextChoices):
        SIGN_IN = "sign_in", "Signed in"
        SIGN_IN_FAILED = "sign_in_failed", "Sign-in failed"
        LOCKED = "locked", "Too many attempts"
        SIGNED_UP = "signed_up", "Signed up"
        SIGNED_OUT = "signed_out", "Signed out"
        PASSWORD_RESET = "password_reset", "Password reset"
        PASSWORD_CHANGED = "password_changed", "Password changed"
        EMAIL_VERIFIED = "email_verified", "Email verified"
        SESSION_REVOKED = "session_revoked", "Session revoked"

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="sign_in_events"
    )
    email = models.EmailField(blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    method = models.CharField(max_length=20, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.created:%Y-%m-%d %H:%M} {self.kind} {self.email}"
