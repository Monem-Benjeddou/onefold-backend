import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import MagicLink, Session, SignInEvent, User

pytestmark = pytest.mark.django_db

BASE = "/api/v1/auth"
STRONG = "correct horse battery"


@pytest.fixture
def client():
    return APIClient()


def register(client, email="ada@example.com", password=STRONG, name="Ada"):
    return client.post(f"{BASE}/register/", {"email": email, "password": password, "name": name})


def login(client, email="ada@example.com", password=STRONG):
    return client.post(f"{BASE}/login/", {"email": email, "password": password})


def token_in(message):
    return re.search(r"token=([\w-]+)", message.body).group(1)


def as_user(access):
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return api


# --- Sign-up -----------------------------------------------------------------


def test_register_signs_in_and_sends_a_confirmation(client):
    response = register(client, email=" Ada@Example.com ")

    assert response.status_code == 201
    data = response.json()
    assert data["created"] is True
    assert data["user"]["email"] == "ada@example.com"
    assert data["user"]["email_verified"] is False
    assert data["user"]["has_password"] is True
    assert data["user"]["onboarding_complete"] is False
    assert as_user(data["access"]).get(f"{BASE}/me/").status_code == 200

    [message] = mail.outbox
    assert message.subject == "Confirm your email for Onefold"
    assert "https://app.onefold.test/verify-email?token=" in message.body
    assert message.alternatives and "Confirm my email" in message.alternatives[0][0]
    assert SignInEvent.objects.filter(kind="signed_up").count() == 1


def test_register_rejects_weak_passwords_with_field_errors(client):
    response = register(client, password="12345")
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "weak_password"
    assert any("too short" in m for m in body["password"])
    assert not User.objects.exists()


def test_register_never_takes_over_an_existing_account(client):
    # e.g. created by a magic link, so it has no password yet
    User.objects.create_user("ada@example.com")
    response = register(client)
    assert response.status_code == 409
    assert response.json()["code"] == "email_taken"
    assert not User.objects.get().has_usable_password()


# --- Password sign-in ----------------------------------------------------------


def test_login_with_the_right_password(client):
    User.objects.create_user("ada@example.com", STRONG)
    response = login(client, email="ADA@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["created"] is False
    assert Session.objects.filter(user__email="ada@example.com", method="password").count() == 1
    assert as_user(data["access"]).get(f"{BASE}/me/").json()["email"] == "ada@example.com"


def test_wrong_password_and_unknown_email_get_the_same_answer(client):
    User.objects.create_user("ada@example.com", STRONG)
    wrong = login(client, password="nope nope nope")
    unknown = login(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]
    assert wrong.json()["code"] == "invalid_credentials"


def test_accounts_without_a_password_cannot_password_sign_in(client):
    User.objects.create_user("ada@example.com")
    assert login(client).status_code == 401


def test_disabled_accounts_cannot_password_sign_in(client):
    User.objects.create_user("ada@example.com", STRONG, is_active=False)
    assert login(client).status_code == 401


def test_repeated_failures_lock_the_email(client, settings):
    settings.LOGIN_MAX_FAILURES = 3
    User.objects.create_user("ada@example.com", STRONG)
    for _ in range(2):
        assert login(client, password="wrong-wrong").status_code == 401

    locked = login(client, password="wrong-wrong")
    assert locked.status_code == 429
    assert locked.json()["code"] == "locked"
    assert locked.json()["retry_after"] > 0
    assert locked["Retry-After"]
    # Even the right password waits until the lock ends.
    assert login(client).status_code == 429
    # Other emails are unaffected.
    User.objects.create_user("grace@example.com", STRONG)
    assert login(client, email="grace@example.com").status_code == 200
    assert SignInEvent.objects.filter(kind="locked").count() == 1


def test_a_successful_sign_in_clears_earlier_failures(client, settings):
    settings.LOGIN_MAX_FAILURES = 3
    User.objects.create_user("ada@example.com", STRONG)
    login(client, password="wrong-wrong")
    login(client, password="wrong-wrong")
    assert login(client).status_code == 200
    login(client, password="wrong-wrong")
    assert login(client, password="wrong-wrong").status_code == 401  # count restarted


def test_auth_endpoints_are_rate_limited_per_ip(client, monkeypatch):
    from rest_framework.throttling import ScopedRateThrottle

    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "2/min"})
    login(client)
    login(client)
    response = login(client)
    assert response.status_code == 429
    assert response.json()["code"] == "throttled"
    assert "request_id" in response.json()


# --- Forgot / reset ------------------------------------------------------------


def test_forgot_password_is_quiet_about_unknown_emails(client):
    response = client.post(f"{BASE}/password/forgot/", {"email": "nobody@example.com"})
    assert response.status_code == 202
    assert not mail.outbox


def test_reset_password_end_to_end(client):
    user = User.objects.create_user("ada@example.com")  # no password yet
    old = login(APIClient(), password="anything-at-all")
    assert old.status_code == 401

    assert client.post(f"{BASE}/password/forgot/", {"email": "ada@example.com"}).status_code == 202
    [message] = mail.outbox
    assert message.subject == "Reset your Onefold password"
    token = token_in(message)

    # A weak password doesn't burn the link.
    weak = client.post(f"{BASE}/password/reset/", {"token": token, "password": "short"})
    assert weak.status_code == 400 and weak.json()["code"] == "weak_password"

    done = client.post(f"{BASE}/password/reset/", {"token": token, "password": STRONG})
    assert done.status_code == 200
    assert done.json()["access"]

    user.refresh_from_db()
    assert user.check_password(STRONG)
    assert user.email_verified  # the reset link proved the inbox
    assert login(APIClient()).status_code == 200

    again = client.post(f"{BASE}/password/reset/", {"token": token, "password": STRONG + "x"})
    assert again.json()["code"] == "used"


def test_reset_signs_out_every_device(client):
    User.objects.create_user("ada@example.com", STRONG)
    first = login(APIClient()).json()
    client.post(f"{BASE}/password/forgot/", {"email": "ada@example.com"})
    client.post(
        f"{BASE}/password/reset/", {"token": token_in(mail.outbox[0]), "password": STRONG + "!"}
    )
    assert as_user(first["access"]).get(f"{BASE}/me/").status_code == 401
    assert client.post(f"{BASE}/token/refresh/", {"refresh": first["refresh"]}).status_code == 401


def test_expired_reset_links(client):
    User.objects.create_user("ada@example.com", STRONG)
    client.post(f"{BASE}/password/forgot/", {"email": "ada@example.com"})
    MagicLink.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    response = client.post(
        f"{BASE}/password/reset/", {"token": token_in(mail.outbox[0]), "password": STRONG + "!"}
    )
    assert response.json()["code"] == "expired"


def test_reset_links_cannot_be_used_as_sign_in_links(client):
    User.objects.create_user("ada@example.com", STRONG)
    client.post(f"{BASE}/password/forgot/", {"email": "ada@example.com"})
    response = client.post(f"{BASE}/magic-link/verify/", {"token": token_in(mail.outbox[0])})
    assert response.json()["code"] == "invalid"


def test_change_password_keeps_this_device_only(client):
    User.objects.create_user("ada@example.com", STRONG)
    other = login(APIClient()).json()
    mine = login(APIClient()).json()
    api = as_user(mine["access"])

    wrong = api.post(
        f"{BASE}/password/change/", {"current_password": "nope", "new_password": STRONG + "!"}
    )
    assert wrong.status_code == 401

    ok = api.post(
        f"{BASE}/password/change/", {"current_password": STRONG, "new_password": STRONG + "!"}
    )
    assert ok.status_code == 204
    assert api.get(f"{BASE}/me/").status_code == 200
    assert as_user(other["access"]).get(f"{BASE}/me/").status_code == 401


# --- Email verification -------------------------------------------------------


def test_verify_email_link(client):
    register(client)
    token = token_in(mail.outbox[0])
    response = client.post(f"{BASE}/email/verify/", {"token": token})
    assert response.status_code == 200
    assert User.objects.get().email_verified
    assert client.post(f"{BASE}/email/verify/", {"token": token}).json()["code"] == "used"


def test_resend_verification_has_a_cooldown():
    data = register(APIClient()).json()
    api = as_user(data["access"])
    assert api.post(f"{BASE}/email/resend/").status_code == 202
    assert len(mail.outbox) == 1  # inside the cooldown: no second email


# --- Sessions / devices -----------------------------------------------------------


def test_list_and_revoke_devices():
    User.objects.create_user("ada@example.com", STRONG)
    laptop = login(APIClient(HTTP_USER_AGENT="Laptop")).json()
    phone = login(APIClient(HTTP_USER_AGENT="Phone")).json()
    api = as_user(laptop["access"])

    sessions = api.get(f"{BASE}/sessions/").json()
    assert len(sessions) == 2
    assert [s["user_agent"] for s in sessions if s["current"]] == ["Laptop"]

    phone_id = next(s["id"] for s in sessions if not s["current"])
    assert api.delete(f"{BASE}/sessions/{phone_id}/").status_code == 204
    assert as_user(phone["access"]).get(f"{BASE}/me/").status_code == 401
    assert api.get(f"{BASE}/me/").status_code == 200


def test_revoke_other_devices():
    User.objects.create_user("ada@example.com", STRONG)
    sessions = [login(APIClient()).json() for _ in range(3)]
    api = as_user(sessions[0]["access"])
    assert api.post(f"{BASE}/sessions/revoke-others/").json() == {"revoked": 2}
    assert as_user(sessions[1]["access"]).get(f"{BASE}/me/").status_code == 401
    assert api.get(f"{BASE}/me/").status_code == 200


def test_sessions_of_other_people_are_invisible():
    User.objects.create_user("ada@example.com", STRONG)
    User.objects.create_user("grace@example.com", STRONG)
    ada = login(APIClient()).json()
    grace = login(APIClient(), email="grace@example.com").json()
    grace_session = as_user(grace["access"]).get(f"{BASE}/sessions/").json()[0]["id"]
    assert as_user(ada["access"]).delete(f"{BASE}/sessions/{grace_session}/").status_code == 404


def test_logout_ends_this_device_session():
    User.objects.create_user("ada@example.com", STRONG)
    data = login(APIClient()).json()
    assert APIClient().post(f"{BASE}/logout/", {"refresh": data["refresh"]}).status_code == 204
    assert as_user(data["access"]).get(f"{BASE}/me/").status_code == 401
    assert SignInEvent.objects.filter(kind="signed_out").count() == 1


def test_logout_with_a_bad_token_still_succeeds(client):
    assert client.post(f"{BASE}/logout/", {"refresh": "garbage"}).status_code == 204


# --- Config & demo ------------------------------------------------------------------


def test_config_lists_the_ways_in(client, settings):
    settings.GITHUB_CLIENT_ID = "id"
    settings.GITHUB_CLIENT_SECRET = "secret"
    settings.DEMO_LOGIN = False
    data = client.get(f"{BASE}/config/").json()
    assert data["password"] and data["magic_link"]
    assert data["providers"] == ["github"]
    assert data["demo"] is False


def test_demo_sign_in_only_in_development(client, settings):
    User.objects.create_user("ada@onefold.local", name="Ada")
    User.objects.create_user("real@example.com")

    settings.DEMO_LOGIN = False
    assert client.get(f"{BASE}/demo/").status_code == 404
    assert client.post(f"{BASE}/demo/", {"email": "ada@onefold.local"}).status_code == 404

    settings.DEMO_LOGIN = True
    assert client.get(f"{BASE}/demo/").json() == [
        {"email": "ada@onefold.local", "name": "Ada", "stage": "Just started, station 1"}
    ]
    assert client.post(f"{BASE}/demo/", {"email": "ada@onefold.local"}).status_code == 200
    # Never for real accounts or staff.
    assert client.post(f"{BASE}/demo/", {"email": "real@example.com"}).status_code == 404
    User.objects.create_superuser("admin@onefold.local", STRONG)
    assert client.post(f"{BASE}/demo/", {"email": "admin@onefold.local"}).status_code == 404


def test_errors_carry_a_request_id(client):
    response = login(client)
    assert response.json()["request_id"] == response["X-Request-ID"]
