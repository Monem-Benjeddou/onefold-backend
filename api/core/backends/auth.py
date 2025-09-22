from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UsernameEmailPhoneNumberAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(username=username) | Q(email=username) | Q(phone_number=username)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False or who haven't been active recently.

        Checks:
        1. User must be active (is_active=True)
        2. User must have logged in within last 30 days OR been created within 30 days
        """

        if not getattr(user, "is_active", True):
            return False

        thirty_days_ago = timezone.now() - timedelta(days=30)
        return (
            user.last_login
            and user.last_login >= thirty_days_ago
            or user.created >= thirty_days_ago
        )
