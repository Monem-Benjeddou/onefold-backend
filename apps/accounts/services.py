"""
Passwordless sign-in.

1. `request_link(email)` stores a hashed single-use token and emails a link
   to the web app (`FRONTEND_URL/auth/verify?token=...`).
2. The web app posts the token to `redeem_link`, which marks it used,
   creates the account on first sign-in, and returns the user.

Requests never reveal whether an account exists.
"""

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import MagicLink, User


class InvalidLink(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_link(email, ttl_minutes=None):
    """Store a new single-use token for `email` and return its sign-in URL."""
    token = secrets.token_urlsafe(32)
    MagicLink.objects.create(
        email=email.strip().lower(),
        token_hash=_hash(token),
        expires_at=timezone.now()
        + timedelta(minutes=ttl_minutes or settings.MAGIC_LINK_TTL_MINUTES),
    )
    return f"{settings.FRONTEND_URL}/auth/verify?{urlencode({'token': token})}"


def request_link(email):
    """Email a sign-in link. Returns False when throttled (caller still answers 202)."""
    email = email.strip().lower()
    cooldown = timezone.now() - timedelta(seconds=settings.MAGIC_LINK_COOLDOWN_SECONDS)
    if MagicLink.objects.filter(email=email, created__gte=cooldown).exists():
        return False

    link = issue_link(email)
    minutes = settings.MAGIC_LINK_TTL_MINUTES
    send_mail(
        subject="Your Onefold sign-in link",
        message=(
            f"Sign in to Onefold:\n\n{link}\n\n"
            f"The link works once and expires in {minutes} minutes. "
            "If you didn't ask for it, ignore this email."
        ),
        from_email=None,
        recipient_list=[email],
    )
    return True


@transaction.atomic
def redeem_link(token):
    """Consume a token. Returns ``(user, created)`` or raises InvalidLink."""
    link = MagicLink.objects.select_for_update().filter(token_hash=_hash(token)).first()
    if link is None:
        raise InvalidLink("That sign-in link isn't valid. Request a new one.", "invalid")
    if link.used_at:
        raise InvalidLink("That link was already used. Request a new one.", "used")
    if link.expires_at <= timezone.now():
        raise InvalidLink("That link expired. Request a new one.", "expired")

    link.used_at = timezone.now()
    link.save(update_fields=["used_at", "updated"])

    user, created = User.objects.get_or_create(email=link.email)
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    if not user.is_active:
        raise InvalidLink("This account is disabled.", "inactive")
    return user, created
