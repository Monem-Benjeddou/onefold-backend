from urllib.parse import parse_qs, urlsplit

import pytest
from rest_framework.test import APIClient

from apps.accounts import oauth
from apps.accounts.models import SocialAccount, User

pytestmark = pytest.mark.django_db

BASE = "/api/v1/auth/oauth"


@pytest.fixture(autouse=True)
def providers(settings):
    settings.GITHUB_CLIENT_ID = "gh-id"
    settings.GITHUB_CLIENT_SECRET = "gh-secret"
    settings.GOOGLE_CLIENT_ID = "g-id"
    settings.GOOGLE_CLIENT_SECRET = "g-secret"


@pytest.fixture
def client():
    return APIClient()


def fake_github(monkeypatch, uid=7, emails=None, token="gho_token"):
    emails = (
        emails
        if emails is not None
        else [{"email": "Ada@Example.com", "primary": True, "verified": True}]
    )
    calls = []

    def http_json(url, data=None, token=None):
        calls.append((url, data, token))
        if url.endswith("/access_token"):
            return {"access_token": "gho_token"} if data["code"] == "good" else {"error": "bad"}
        if url.endswith("/user"):
            return {"id": uid, "login": "ada", "name": "Ada Lovelace"}
        if url.endswith("/user/emails"):
            return emails
        raise AssertionError(url)

    monkeypatch.setattr(oauth, "http_json", http_json)
    return calls


def start(client, provider="github", next_path="/path"):
    return client.post(f"{BASE}/{provider}/start/", {"next": next_path}).json()


def test_start_returns_the_consent_url(client):
    data = start(client)
    url = urlsplit(data["authorize_url"])
    query = parse_qs(url.query)
    assert url.netloc == "github.com"
    assert query["client_id"] == ["gh-id"]
    assert query["redirect_uri"] == ["https://app.onefold.test/api/auth/oauth/github/callback"]
    assert query["state"] == [data["state"]]
    assert "gh-secret" not in data["authorize_url"]


def test_disabled_providers_are_refused(client, settings):
    settings.GOOGLE_CLIENT_SECRET = ""
    response = client.post(f"{BASE}/google/start/")
    assert response.status_code == 400
    assert response.json()["code"] == "provider_disabled"
    assert client.post(f"{BASE}/myspace/start/").json()["code"] == "provider_disabled"


def test_first_github_sign_in_creates_a_verified_account(client, monkeypatch):
    calls = fake_github(monkeypatch)
    state = start(client)["state"]

    response = client.post(f"{BASE}/github/callback/", {"code": "good", "state": state})

    assert response.status_code == 200
    data = response.json()
    assert data["created"] is True
    assert data["next"] == "/path"
    user = User.objects.get()
    assert user.email == "ada@example.com" and user.name == "Ada Lovelace"
    assert user.email_verified and not user.has_usable_password()
    assert SocialAccount.objects.get().login == "ada"
    # The secret is only ever sent to GitHub's token endpoint.
    assert calls[0][1]["client_secret"] == "gh-secret"


def test_github_links_to_an_existing_account_by_verified_email(client, monkeypatch):
    existing = User.objects.create_user("ada@example.com", "correct horse battery")
    fake_github(monkeypatch)
    data = client.post(
        f"{BASE}/github/callback/", {"code": "good", "state": start(client)["state"]}
    ).json()
    assert data["created"] is False
    assert data["user"]["id"] == str(existing.id)
    assert data["user"]["connected"] == ["github"]

    # Next time, matched by GitHub id even if the email there changed.
    fake_github(monkeypatch, emails=[{"email": "new@x.com", "primary": True, "verified": True}])
    again = client.post(
        f"{BASE}/github/callback/", {"code": "good", "state": start(client)["state"]}
    ).json()
    assert again["user"]["id"] == str(existing.id)
    assert User.objects.count() == 1


def test_unverified_emails_are_never_linked(client, monkeypatch):
    User.objects.create_user("ada@example.com", "correct horse battery")
    fake_github(
        monkeypatch, emails=[{"email": "ada@example.com", "primary": True, "verified": False}]
    )
    response = client.post(
        f"{BASE}/github/callback/", {"code": "good", "state": start(client)["state"]}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "no_verified_email"
    assert not SocialAccount.objects.exists()


def test_state_must_be_ours_and_for_this_provider(client, monkeypatch):
    fake_github(monkeypatch)
    google_state = start(client, "google")["state"]
    wrong_provider = client.post(
        f"{BASE}/github/callback/", {"code": "good", "state": google_state}
    )
    assert wrong_provider.json()["code"] == "state_invalid"
    forged = client.post(f"{BASE}/github/callback/", {"code": "good", "state": "forged"})
    assert forged.json()["code"] == "state_invalid"


def test_denied_consent(client, monkeypatch):
    fake_github(monkeypatch)
    response = client.post(
        f"{BASE}/github/callback/", {"code": "bad", "state": start(client)["state"]}
    )
    assert response.json()["code"] == "provider_denied"


def test_google_sign_in(client, monkeypatch):
    def http_json(url, data=None, token=None):
        if "token" in url:
            return {"access_token": "ya29"}
        return {"sub": "123", "email": "grace@example.com", "email_verified": True, "name": "Grace"}

    monkeypatch.setattr(oauth, "http_json", http_json)
    data = client.post(
        f"{BASE}/google/callback/", {"code": "c", "state": start(client, "google")["state"]}
    ).json()
    assert data["created"] is True
    assert data["user"]["connected"] == ["google"]
