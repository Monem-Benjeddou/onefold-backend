"""
Authentication rules.

Ways in:
- **Password**: ``register`` then ``authenticate_password``. Failed attempts per
  email are counted; too many lock that email out for a while.
- **Magic link**: ``request_link`` emails a single-use link; ``redeem_link``
  consumes it and creates the account on first use.
- **GitHub / Google**: see ``oauth.py``.

Every successful sign-in goes through ``start_session``, which records the
device as a ``Session`` and puts its id in the tokens (the ``sid`` claim), so a
session can be revoked from another device.

Requests that email someone (magic link, forgot password) never reveal whether
an account exists.
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import MagicLink, Session, SignInEvent, User

logger = logging.getLogger(__name__)

Purpose = MagicLink.Purpose


# --- Errors -------------------------------------------------------------------


class AuthError(Exception):
    """An authentication failure with a stable ``code`` for the client."""

    status = 400

    def __init__(self, message, code, retry_after=None):
        super().__init__(message)
        self.code = code
        self.retry_after = retry_after


class InvalidLink(AuthError):
    pass


class InvalidCredentials(AuthError):
    status = 401


class LockedOut(AuthError):
    status = 429


class EmailTaken(AuthError):
    status = 409


# --- Request context & audit -------------------------------------------------


@dataclass
class Client:
    ip: str | None = None
    user_agent: str = ""

    @classmethod
    def from_request(cls, request):
        if request is None:
            return cls()
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
        return cls(ip=ip or None, user_agent=request.META.get("HTTP_USER_AGENT", "")[:300])


def record(kind, client, user=None, email="", method=""):
    SignInEvent.objects.create(
        user=user,
        email=(email or getattr(user, "email", ""))[:254],
        kind=kind,
        method=method,
        ip=client.ip,
        user_agent=client.user_agent,
    )


def normalize(email):
    return email.strip().lower()


# --- Sessions -----------------------------------------------------------------


def start_session(user, client, method):
    """Sign ``user`` in on this device. Returns ``(session, access, refresh)``."""
    session = Session.objects.create(
        user=user, method=method, user_agent=client.user_agent, ip=client.ip
    )
    refresh = RefreshToken.for_user(user)
    refresh["sid"] = str(session.id)
    update_last_login(None, user)
    record(SignInEvent.Kind.SIGN_IN, client, user=user, method=method)
    return session, str(refresh.access_token), str(refresh)


def revoke_session(session, client=None):
    if session.revoked_at is None:
        session.revoked_at = timezone.now()
        session.save(update_fields=["revoked_at", "updated"])
        if client is not None:
            record(SignInEvent.Kind.SESSION_REVOKED, client, user=session.user)


def revoke_all_sessions(user, keep=None):
    sessions = Session.objects.filter(user=user, revoked_at__isnull=True)
    if keep is not None:
        sessions = sessions.exclude(pk=keep)
    return sessions.update(revoked_at=timezone.now())


def session_is_active(session_id, user_id=None):
    sessions = Session.objects.filter(pk=session_id, revoked_at__isnull=True)
    if user_id is not None:
        sessions = sessions.filter(user_id=user_id)
    return sessions.exists()


# --- Lockout for failed password attempts --------------------------------------


def _key(kind, email):
    return f"auth:{kind}:{hashlib.sha256(email.encode()).hexdigest()}"


def locked_for(email):
    """Seconds until ``email`` may try a password again (0 when not locked)."""
    until = cache.get(_key("locked", email))
    if until is None:
        return 0
    return max(0, int(until - timezone.now().timestamp()))


def _record_failure(email):
    """Count a failed attempt. Returns True when this failure locks the email."""
    window = settings.LOGIN_LOCKOUT_MINUTES * 60
    key = _key("fail", email)
    cache.add(key, 0, window)
    try:
        failures = cache.incr(key)
    except ValueError:  # expired between add and incr
        cache.set(key, 1, window)
        failures = 1
    if failures >= settings.LOGIN_MAX_FAILURES:
        cache.set(_key("locked", email), timezone.now().timestamp() + window, window)
        cache.delete(key)
        return True
    return False


def clear_failures(email):
    cache.delete_many([_key("fail", email), _key("locked", email)])


def _lockout_error(seconds):
    minutes = max(1, -(-seconds // 60))
    return LockedOut(
        f"Too many attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}, "
        "or reset your password.",
        "locked",
        retry_after=seconds,
    )


# --- Password sign-in & sign-up ---------------------------------------------


def authenticate_password(email, password, client, request=None):
    email = normalize(email)
    wait = locked_for(email)
    if wait:
        raise _lockout_error(wait)

    # Django's backend runs the hasher even for unknown emails (constant time),
    # and refuses inactive accounts.
    user = authenticate(request, username=email, password=password)
    if user is None:
        known = User.objects.filter(email=email).first()
        record(SignInEvent.Kind.SIGN_IN_FAILED, client, user=known, email=email, method="password")
        if _record_failure(email):
            record(SignInEvent.Kind.LOCKED, client, user=known, email=email, method="password")
            raise _lockout_error(settings.LOGIN_LOCKOUT_MINUTES * 60)
        raise InvalidCredentials("That email and password don't match.", "invalid_credentials")
    clear_failures(email)
    return user


def check_new_password(password, email="", name=""):
    """Raise Django's ValidationError (a list of messages) if the password is weak."""
    validate_password(password, user=User(email=normalize(email) if email else "", name=name))


def register(email, password, name, client):
    email = normalize(email)
    if User.objects.filter(email=email).exists():
        raise EmailTaken("An account with this email already exists.", "email_taken")
    check_new_password(password, email, name)
    try:
        with transaction.atomic():
            user = User.objects.create_user(email, password, name=name.strip())
    except IntegrityError:
        raise EmailTaken("An account with this email already exists.", "email_taken") from None
    record(SignInEvent.Kind.SIGNED_UP, client, user=user, method="password")
    send_verification(user)
    return user


def change_password(user, current, new, client, keep_session=None):
    if user.has_usable_password() and not user.check_password(current or ""):
        raise InvalidCredentials("Your current password isn't right.", "wrong_password")
    check_new_password(new, user.email, user.name)
    user.set_password(new)
    user.save(update_fields=["password", "updated"])
    revoke_all_sessions(user, keep=keep_session)
    record(SignInEvent.Kind.PASSWORD_CHANGED, client, user=user)


# --- Emailed tokens -------------------------------------------------------------

_LINK_PAGES = {
    Purpose.SIGN_IN: "/auth/verify",
    Purpose.PASSWORD_RESET: "/reset-password",
    Purpose.VERIFY_EMAIL: "/verify-email",
}


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _issue(email, purpose, ttl):
    token = secrets.token_urlsafe(32)
    MagicLink.objects.create(
        email=normalize(email),
        purpose=purpose,
        token_hash=_hash(token),
        expires_at=timezone.now() + ttl,
    )
    return f"{settings.FRONTEND_URL}{_LINK_PAGES[purpose]}?{urlencode({'token': token})}"


def _in_cooldown(email, purpose):
    since = timezone.now() - timedelta(seconds=settings.MAGIC_LINK_COOLDOWN_SECONDS)
    return MagicLink.objects.filter(email=email, purpose=purpose, created__gte=since).exists()


def _find_open(token, purpose, noun):
    """The unused, unexpired token row (locked for update), or InvalidLink."""
    link = (
        MagicLink.objects.select_for_update()
        .filter(token_hash=_hash(token or ""), purpose=purpose)
        .first()
    )
    if link is None:
        raise InvalidLink(f"That {noun} isn't valid. Request a new one.", "invalid")
    if link.used_at:
        raise InvalidLink(f"That {noun} was already used. Request a new one.", "used")
    if link.expires_at <= timezone.now():
        raise InvalidLink(f"That {noun} expired. Request a new one.", "expired")
    return link


def _use(link):
    link.used_at = timezone.now()
    link.save(update_fields=["used_at", "updated"])


def send_email(template, to, subject, **context):
    """Render ``accounts/email/<template>.{txt,html}`` and send it. Never raises."""
    context = {"subject": subject, "frontend_url": settings.FRONTEND_URL, **context}
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(f"accounts/email/{template}.txt", context),
        to=[to],
    )
    message.attach_alternative(
        render_to_string(f"accounts/email/{template}.html", context), "text/html"
    )
    try:
        message.send()
    except Exception:
        # Email trouble must never break a sign-in flow (or reveal anything).
        logger.exception("Could not send the %s email", template)
        return False
    return True


# Magic links


def issue_link(email, ttl_minutes=None):
    """Store a new single-use sign-in token for ``email`` and return its URL."""
    ttl = timedelta(minutes=ttl_minutes or settings.MAGIC_LINK_TTL_MINUTES)
    return _issue(email, Purpose.SIGN_IN, ttl)


def request_link(email):
    """Email a sign-in link. Returns False when throttled (callers still answer 202)."""
    email = normalize(email)
    if _in_cooldown(email, Purpose.SIGN_IN):
        return False
    send_email(
        "sign_in",
        email,
        "Your Onefold sign-in link",
        link=issue_link(email),
        minutes=settings.MAGIC_LINK_TTL_MINUTES,
    )
    return True


@transaction.atomic
def redeem_link(token):
    """Consume a sign-in token. Returns ``(user, created)`` or raises InvalidLink."""
    link = _find_open(token, Purpose.SIGN_IN, "sign-in link")
    _use(link)
    user, created = User.objects.get_or_create(email=link.email)
    if created:
        user.set_unusable_password()
    if not user.is_active:
        raise InvalidLink("This account is disabled.", "inactive")
    # Opening the link proves the inbox.
    user.email_verified_at = user.email_verified_at or timezone.now()
    user.save()
    return user, created


# Email verification


def send_verification(user):
    if user.email_verified or _in_cooldown(user.email, Purpose.VERIFY_EMAIL):
        return False
    hours = settings.VERIFY_EMAIL_TTL_HOURS
    link = _issue(user.email, Purpose.VERIFY_EMAIL, timedelta(hours=hours))
    return send_email(
        "verify_email",
        user.email,
        "Confirm your email for Onefold",
        link=link,
        hours=hours,
        user=user,
    )


@transaction.atomic
def verify_email(token, client):
    link = _find_open(token, Purpose.VERIFY_EMAIL, "confirmation link")
    _use(link)
    user = User.objects.filter(email=link.email).first()
    if user is None:
        raise InvalidLink("That confirmation link isn't valid. Request a new one.", "invalid")
    if not user.email_verified:
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at", "updated"])
        record(SignInEvent.Kind.EMAIL_VERIFIED, client, user=user)
    return user


# Password reset


def forgot_password(email):
    """Email a reset link if the account exists. Always quiet about the outcome."""
    email = normalize(email)
    user = User.objects.filter(email=email, is_active=True).first()
    if user is None or _in_cooldown(email, Purpose.PASSWORD_RESET):
        return False
    minutes = settings.PASSWORD_RESET_TTL_MINUTES
    link = _issue(email, Purpose.PASSWORD_RESET, timedelta(minutes=minutes))
    send_email(
        "password_reset",
        email,
        "Reset your Onefold password",
        link=link,
        minutes=minutes,
        user=user,
    )
    return True


@transaction.atomic
def reset_password(token, password, client):
    """
    Set a new password from a reset link. The password is checked before the
    link is used, so a weak password doesn't burn the link. Signs out every
    device.
    """
    link = _find_open(token, Purpose.PASSWORD_RESET, "reset link")
    user = User.objects.filter(email=link.email, is_active=True).first()
    if user is None:
        raise InvalidLink("That reset link isn't valid. Request a new one.", "invalid")
    check_new_password(password, user.email, user.name)
    _use(link)
    user.set_password(password)
    user.email_verified_at = user.email_verified_at or timezone.now()
    user.save()
    revoke_all_sessions(user)
    clear_failures(user.email)
    record(SignInEvent.Kind.PASSWORD_RESET, client, user=user)
    return user
