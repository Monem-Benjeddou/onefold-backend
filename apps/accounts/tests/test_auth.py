import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import MagicLink, User

pytestmark = pytest.mark.django_db

BASE = "/api/v1/auth"


def request_link(client, email="ada@example.com"):
    return client.post(f"{BASE}/magic-link/", {"email": email})


def token_from_email(message):
    return re.search(r"token=([\w-]+)", message.body).group(1)


@pytest.fixture
def client():
    return APIClient()


def test_full_sign_in_creates_the_account(client):
    response = request_link(client, "Ada@Example.com ")

    assert response.status_code == 202
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["ada@example.com"]
    assert "https://app.onefold.test/auth/verify?token=" in message.body
    assert MagicLink.objects.get().token_hash != token_from_email(message)  # stored hashed

    signed_in = client.post(f"{BASE}/magic-link/verify/", {"token": token_from_email(message)})

    assert signed_in.status_code == 200
    data = signed_in.json()
    assert data["created"] is True
    assert data["user"]["email"] == "ada@example.com"
    user = User.objects.get(email="ada@example.com")
    assert not user.has_usable_password()
    assert user.last_login is not None

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
    assert client.get(f"{BASE}/me/").json()["email"] == "ada@example.com"


def test_existing_users_sign_in_without_duplicates(client):
    User.objects.create_user("ada@example.com")
    request_link(client)
    data = client.post(
        f"{BASE}/magic-link/verify/", {"token": token_from_email(mail.outbox[0])}
    ).json()
    assert data["created"] is False
    assert User.objects.count() == 1


def test_links_are_single_use(client):
    request_link(client)
    token = token_from_email(mail.outbox[0])
    assert client.post(f"{BASE}/magic-link/verify/", {"token": token}).status_code == 200

    again = client.post(f"{BASE}/magic-link/verify/", {"token": token})
    assert again.status_code == 400
    assert again.json()["code"] == "used"


def test_expired_and_unknown_links(client):
    request_link(client)
    token = token_from_email(mail.outbox[0])
    MagicLink.objects.update(expires_at=timezone.now() - timedelta(seconds=1))

    assert client.post(f"{BASE}/magic-link/verify/", {"token": token}).json()["code"] == "expired"
    assert client.post(f"{BASE}/magic-link/verify/", {"token": "nope"}).json()["code"] == "invalid"


def test_requests_are_throttled_per_email_without_revealing_it(client):
    assert request_link(client).status_code == 202
    assert request_link(client).status_code == 202
    assert len(mail.outbox) == 1
    assert request_link(client, "grace@example.com").status_code == 202
    assert len(mail.outbox) == 2


def test_disabled_accounts_cannot_sign_in(client):
    User.objects.create_user("ada@example.com", is_active=False)
    request_link(client)
    response = client.post(
        f"{BASE}/magic-link/verify/", {"token": token_from_email(mail.outbox[0])}
    )
    assert response.json()["code"] == "inactive"


def test_refresh_token_rotates(client):
    request_link(client)
    data = client.post(
        f"{BASE}/magic-link/verify/", {"token": token_from_email(mail.outbox[0])}
    ).json()

    refreshed = client.post(f"{BASE}/token/refresh/", {"refresh": data["refresh"]})

    assert refreshed.status_code == 200
    assert {"access", "refresh"} <= set(refreshed.json())
    # The old refresh token is spent once rotated.
    assert client.post(f"{BASE}/token/refresh/", {"refresh": data["refresh"]}).status_code == 401


def test_logout_revokes_the_refresh_token(client):
    request_link(client)
    data = client.post(
        f"{BASE}/magic-link/verify/", {"token": token_from_email(mail.outbox[0])}
    ).json()

    assert client.post(f"{BASE}/logout/", {"refresh": data["refresh"]}).status_code == 200
    assert client.post(f"{BASE}/token/refresh/", {"refresh": data["refresh"]}).status_code == 401


def test_me_update_and_delete():
    user = User.objects.create_user("ada@example.com")
    client = APIClient()
    client.force_authenticate(user)

    updated = client.patch(f"{BASE}/me/", {"name": "Ada", "email": "evil@example.com"})
    assert updated.json()["name"] == "Ada"
    assert updated.json()["email"] == "ada@example.com"

    assert client.delete(f"{BASE}/me/").status_code == 204
    assert not User.objects.exists()


def test_me_requires_authentication(client):
    assert client.get(f"{BASE}/me/").status_code == 401


def test_health(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["checks"]["database"] == "ok"
