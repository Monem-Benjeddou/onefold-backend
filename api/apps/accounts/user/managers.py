from django.contrib.auth.models import BaseUserManager
import random
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from core.abstract.models import AbstractManager


class UserManager(BaseUserManager, AbstractManager):
    def create_user(self, email, password=None, **extra_fields):
        if email is None:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email.lower() if email else None)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

    def active(self):
        """Return only active users."""
        return self.filter(is_active=True)

    def inactive(self):
        """Return only inactive users."""
        return self.filter(is_active=False)

    def deactivate_user(self, user_id):
        """
        Deactivate a user account.

        Args:
            user_id: UUID of the user to deactivate

        Returns:
            User instance if successful, None if user not found
        """
        try:
            user = self.get(id=user_id, is_active=True)
            user.is_active = False
            user.deactivated_at = timezone.now()
            user.save(update_fields=["is_active", "deactivated_at", "updated"])
            return user
        except self.model.DoesNotExist:
            return None

    def activate_user(self, user_id):
        """
        Activate a user account.

        Args:
            user_id: UUID of the user to activate

        Returns:
            User instance if successful, None if user not found
        """
        try:
            user = self.get(id=user_id, is_active=False)
            user.is_active = True
            user.deactivated_at = None
            user.save(update_fields=["is_active", "deactivated_at", "updated"])
            return user
        except self.model.DoesNotExist:
            return None

    def recently_deactivated(self, days=30):
        """
        Return users deactivated within the specified number of days.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            QuerySet of recently deactivated users
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(is_active=False, deactivated_at__gte=cutoff_date)

    def with_profiles(self):
        """
        Return users with related profile data optimized for display.

        Prevents N+1 queries by preloading related data.

        Returns:
            QuerySet: Optimized user queryset with related data
        """
        return self.select_related("country").prefetch_related("groups")

    def active_with_roles(self):
        """
        Return active users with role filtering optimization.

        Uses only() to limit fields and prevent unnecessary data transfer.

        Returns:
            QuerySet: Optimized active user queryset
        """
        return (
            self.filter(is_active=True)
            .select_related("country")
            .only(
                "id",
                "email",
                "username",
                "role",
                "is_active",
                "fullname",
                "country__name",
                "is_email_verified",
                "created",
            )
        )

    def by_role(self, role):
        """
        Return users filtered by role with database index optimization.

        Args:
            role: User role to filter by

        Returns:
            QuerySet: Users with specified role
        """
        return self.filter(role=role, is_active=True)

    def banned_users(self):
        """
        Return currently banned users.

        Efficiently filters banned users considering ban expiration.

        Returns:
            QuerySet: Currently banned users
        """
        from django.db.models import Q

        now = timezone.now()

        return self.filter(
            Q(is_banned=True)
            & (Q(ban_expires_at__isnull=True) | Q(ban_expires_at__gt=now))
        ).select_related("banned_by")


class VerificationCodeManager(AbstractManager):
    def create_verification_code(self, user):
        code = "".join(random.choices("0123456789", k=6))
        return self.create(user=user, code=code)

    def validate_code(self, user, code):
        try:
            self.get(user=user, code=code)
            return True
        except ObjectDoesNotExist:
            return False
