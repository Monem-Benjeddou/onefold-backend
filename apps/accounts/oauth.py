"""
Sign in with GitHub or Google (OAuth 2.0 authorization-code flow).

1. ``authorize_url(provider, next)`` returns the provider's consent URL and a
   signed ``state``. The web app keeps the state in an httpOnly cookie and
   redirects the browser.
2. The provider sends the browser back to
   ``FRONTEND_URL/api/auth/oauth/<provider>/callback?code=...&state=...``.
   The web app checks the state matches its cookie, then posts both here.
3. ``complete(provider, code, state)`` checks the state signature and age,
   exchanges the code server-side (the client secret never leaves the API),
   reads the identity and returns ``(user, created, next)``.

Accounts are matched by provider id first, then by **verified** email, so an
existing builder who signs in with GitHub lands in the same account.
"""

import json
import secrets
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import SocialAccount, User
from .services import AuthError, normalize

STATE_SALT = "onefold.oauth.state"
STATE_MAX_AGE = 10 * 60
TIMEOUT = 10


class OAuthError(AuthError):
    pass


@dataclass(frozen=True)
class Provider:
    name: str
    label: str
    authorize: str
    token: str
    scope: str
    extra: tuple = ()

    @property
    def client_id(self):
        return getattr(settings, f"{self.name.upper()}_CLIENT_ID", "")

    @property
    def client_secret(self):
        return getattr(settings, f"{self.name.upper()}_CLIENT_SECRET", "")

    @property
    def enabled(self):
        return bool(self.client_id and self.client_secret)

    @property
    def redirect_uri(self):
        return f"{settings.FRONTEND_URL}/api/auth/oauth/{self.name}/callback"


PROVIDERS = {
    "github": Provider(
        name="github",
        label="GitHub",
        authorize="https://github.com/login/oauth/authorize",
        token="https://github.com/login/oauth/access_token",
        scope="read:user user:email",
        extra=(("allow_signup", "true"),),
    ),
    "google": Provider(
        name="google",
        label="Google",
        authorize="https://accounts.google.com/o/oauth2/v2/auth",
        token="https://oauth2.googleapis.com/token",
        scope="openid email profile",
        extra=(("prompt", "select_account"),),
    ),
}


@dataclass
class Identity:
    uid: str
    email: str
    email_verified: bool
    name: str = ""
    login: str = ""


def enabled_providers():
    return [name for name, provider in PROVIDERS.items() if provider.enabled]


def get_provider(name):
    provider = PROVIDERS.get(name)
    if provider is None or not provider.enabled:
        raise OAuthError(f"Sign-in with {name} isn't set up.", "provider_disabled")
    return provider


def authorize_url(name, next_path=""):
    provider = get_provider(name)
    state = signing.dumps(
        {"p": provider.name, "n": secrets.token_urlsafe(16), "next": next_path[:300]},
        salt=STATE_SALT,
    )
    query = {
        "client_id": provider.client_id,
        "redirect_uri": provider.redirect_uri,
        "response_type": "code",
        "scope": provider.scope,
        "state": state,
        **dict(provider.extra),
    }
    return f"{provider.authorize}?{urlencode(query)}", state


# --- HTTP (patched in tests) -------------------------------------------------


def http_json(url, data=None, token=None):
    """POST a form (when ``data`` is given) or GET, and decode the JSON reply."""
    headers = {"Accept": "application/json", "User-Agent": "Onefold"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = urlencode(data).encode() if data is not None else None
    try:
        with urlopen(Request(url, data=body, headers=headers), timeout=TIMEOUT) as response:  # noqa: S310 - fixed provider URLs
            return json.loads(response.read(1_000_000))
    except (URLError, TimeoutError, ValueError) as error:
        raise OAuthError(
            "We couldn't reach the sign-in provider. Try again.", "provider_error"
        ) from error


def _exchange_code(provider, code):
    reply = http_json(
        provider.token,
        data={
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "code": code,
            "redirect_uri": provider.redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    token = reply.get("access_token") if isinstance(reply, dict) else None
    if not token:
        raise OAuthError("Sign-in was cancelled or expired. Try again.", "provider_denied")
    return token


def _github_identity(token):
    profile = http_json("https://api.github.com/user", token=token)
    emails = http_json("https://api.github.com/user/emails", token=token)
    primary = next(
        (e for e in emails if isinstance(e, dict) and e.get("primary") and e.get("verified")),
        None,
    ) or next((e for e in emails if isinstance(e, dict) and e.get("verified")), None)
    return Identity(
        uid=str(profile["id"]),
        email=normalize(primary["email"]) if primary else "",
        email_verified=bool(primary),
        name=profile.get("name") or "",
        login=profile.get("login") or "",
    )


def _google_identity(token):
    info = http_json("https://openidconnect.googleapis.com/v1/userinfo", token=token)
    return Identity(
        uid=str(info["sub"]),
        email=normalize(info.get("email", "")),
        email_verified=bool(info.get("email_verified")),
        name=info.get("name") or "",
        login=info.get("email", ""),
    )


IDENTITY_READERS = {"github": _github_identity, "google": _google_identity}


# --- Completing sign-in -----------------------------------------------------------


def read_state(name, state):
    try:
        data = signing.loads(state or "", salt=STATE_SALT, max_age=STATE_MAX_AGE)
    except signing.SignatureExpired:
        raise OAuthError("Sign-in took too long. Try again.", "state_expired") from None
    except signing.BadSignature:
        raise OAuthError("Sign-in couldn't be verified. Try again.", "state_invalid") from None
    if data.get("p") != name:
        raise OAuthError("Sign-in couldn't be verified. Try again.", "state_invalid")
    return data


def complete(name, code, state):
    provider = get_provider(name)
    data = read_state(name, state)
    try:
        identity = IDENTITY_READERS[name](_exchange_code(provider, code))
    except (KeyError, TypeError) as error:
        raise OAuthError(
            "The sign-in provider sent an unexpected reply. Try again.", "provider_error"
        ) from error
    user, created = link_identity(name, identity)
    return user, created, data.get("next", "")


@transaction.atomic
def link_identity(provider, identity):
    """Find or create the user for a provider identity. Returns ``(user, created)``."""
    account = (
        SocialAccount.objects.select_related("user")
        .filter(provider=provider, uid=identity.uid)
        .first()
    )
    if account:
        user, created = account.user, False
    else:
        if not identity.email or not identity.email_verified:
            raise OAuthError(
                f"Your {PROVIDERS[provider].label} account has no verified email. "
                "Verify one there, or sign in with email.",
                "no_verified_email",
            )
        user = User.objects.filter(email=identity.email).first()
        created = user is None
        if created:
            user = User.objects.create_user(identity.email, name=identity.name[:120])
        try:
            with transaction.atomic():
                SocialAccount.objects.create(
                    user=user, provider=provider, uid=identity.uid, login=identity.login[:191]
                )
        except IntegrityError:
            raise OAuthError(
                f"This account is already linked to a different {PROVIDERS[provider].label} "
                "account.",
                "already_linked",
            ) from None

    if not user.is_active:
        raise OAuthError("This account is disabled.", "inactive")
    if not user.email_verified and identity.email == user.email and identity.email_verified:
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at", "updated"])
    return user, created
