from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


def was_user_created_recently(user, minutes=5):
    """
    Check if a user was created within the last few minutes.

    Parameters:
    - user_id: The ID of the user to check.
    - minutes: The time window in minutes to consider as "recently". Default is 5 minutes.

    Returns:
    - True if the user was created within the last few minutes, False otherwise.
    """
    try:
        now = timezone.now()
        time_difference = now - user.created
        return time_difference <= timedelta(minutes=minutes)
    except User.DoesNotExist:
        return False
