from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

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
            # Builders sign in with magic links; only staff need passwords.
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

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.email


class MagicLink(TimeStampedModel):
    """A single-use sign-in link. Only a hash of the token is stored."""

    email = models.EmailField(db_index=True)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.email} ({'used' if self.used_at else 'open'})"
