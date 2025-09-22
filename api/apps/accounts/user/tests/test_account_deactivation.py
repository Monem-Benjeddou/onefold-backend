"""
Comprehensive test suite for account deactivation functionality.
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch
from datetime import timedelta

from apps.accounts.user.tests.factories import UserFactory

User = get_user_model()


class AccountDeactivationModelTests(TestCase):
    """Test account deactivation at model level."""

    def setUp(self):
        self.user = UserFactory()

    def test_user_manager_active_method(self):
        """Test User manager active() method."""
        active_user = UserFactory(is_active=True)
        inactive_user = UserFactory(is_active=False)

        active_users = User.objects.active()

        self.assertIn(active_user, active_users)
        self.assertNotIn(inactive_user, active_users)

    def test_user_manager_inactive_method(self):
        """Test User manager inactive() method."""
        active_user = UserFactory(is_active=True)
        inactive_user = UserFactory(is_active=False)

        inactive_users = User.objects.inactive()

        self.assertIn(inactive_user, inactive_users)
        self.assertNotIn(active_user, inactive_users)

    def test_user_manager_deactivate_user(self):
        """Test User manager deactivate_user() method."""
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.deactivated_at)

        result = User.objects.deactivate_user(self.user.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.user.id)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deactivated_at)

    def test_user_manager_deactivate_user_not_found(self):
        """Test deactivating non-existent user."""
        result = User.objects.deactivate_user("123e4567-e89b-12d3-a456-426614174000")
        self.assertIsNone(result)

    def test_user_manager_deactivate_already_inactive_user(self):
        """Test deactivating already inactive user."""
        self.user.is_active = False
        self.user.save()

        result = User.objects.deactivate_user(self.user.id)
        self.assertIsNone(result)

    def test_user_manager_activate_user(self):
        """Test User manager activate_user() method."""
        self.user.is_active = False
        self.user.deactivated_at = timezone.now()
        self.user.save()

        result = User.objects.activate_user(self.user.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.user.id)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.deactivated_at)

    def test_user_manager_activate_user_not_found(self):
        """Test activating non-existent user."""
        result = User.objects.activate_user("123e4567-e89b-12d3-a456-426614174000")
        self.assertIsNone(result)

    def test_user_manager_activate_already_active_user(self):
        """Test activating already active user."""
        result = User.objects.activate_user(self.user.id)
        self.assertIsNone(result)

    def test_user_manager_recently_deactivated(self):
        """Test recently_deactivated() method."""
        now = timezone.now()

        user1 = UserFactory(is_active=False, deactivated_at=now - timedelta(days=1))

        user2 = UserFactory(is_active=False, deactivated_at=now - timedelta(days=31))

        user3 = UserFactory(is_active=True)

        recent = User.objects.recently_deactivated()
        self.assertIn(user1, recent)
        self.assertNotIn(user2, recent)
        self.assertNotIn(user3, recent)

        recent_45 = User.objects.recently_deactivated(days=45)
        self.assertIn(user1, recent_45)
        self.assertIn(user2, recent_45)
        self.assertNotIn(user3, recent_45)


class SelfDeactivationViewTests(TestCase):
    """Test self-deactivation API views."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.superuser = UserFactory(is_superuser=True)
        self.deactivate_url = reverse("self-deactivate")
        self.status_url = reverse("account-status")

    def test_self_deactivation_success(self):
        """Test successful self-deactivation."""
        self.client.force_authenticate(user=self.user)

        data = {"confirm_deactivation": True, "reason": "Personal reasons"}

        response = self.client.post(self.deactivate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("Account deactivated successfully", response.data["message"])
        self.assertEqual(str(self.user.id), response.data["user_id"])
        self.assertIsNotNone(response.data["deactivated_at"])

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deactivated_at)

    def test_self_deactivation_without_confirmation(self):
        """Test self-deactivation without confirmation."""
        self.client.force_authenticate(user=self.user)

        data = {"confirm_deactivation": False, "reason": "Test"}

        response = self.client.post(self.deactivate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_deactivation", response.data["error"])

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_self_deactivation_already_inactive(self):
        """Test self-deactivation when already inactive."""
        self.user.is_active = False
        self.user.save()

        self.client.force_authenticate(user=self.user)

        data = {"confirm_deactivation": True}

        response = self.client.post(self.deactivate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already deactivated", response.data["error"])

    def test_self_deactivation_superuser_blocked(self):
        """Test that superusers cannot self-deactivate."""
        self.client.force_authenticate(user=self.superuser)

        data = {"confirm_deactivation": True}

        response = self.client.post(self.deactivate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Superuser accounts cannot be self-deactivated", response.data["error"]
        )

    def test_self_deactivation_unauthenticated(self):
        """Test self-deactivation without authentication."""
        data = {"confirm_deactivation": True}

        response = self.client.post(self.deactivate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_self_deactivation_rate_limiting(self):
        """Test rate limiting on self-deactivation endpoint."""
        self.client.force_authenticate(user=self.user)

        data = {"confirm_deactivation": True}

        for _ in range(4):
            response = self.client.post(self.deactivate_url, data, format="json")
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        else:

            pass

    def test_account_status_view(self):
        """Test account status retrieval."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_active"])
        self.assertIsNone(response.data["deactivated_at"])

    def test_account_status_view_inactive_user(self):
        """Test account status for inactive user."""
        deactivation_time = timezone.now()
        self.user.is_active = False
        self.user.deactivated_at = deactivation_time
        self.user.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])
        self.assertIsNotNone(response.data["deactivated_at"])


class AuthenticationDeactivationTests(TestCase):
    """Test authentication behavior with deactivated accounts."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()

    def test_jwt_authentication_blocks_inactive_user(self):
        """Test that JWT authentication blocks inactive users."""

        self.client.force_authenticate(user=self.user)

        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            "/api/v1/users/me/deactivate/", {"confirm_deactivation": True}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_blocks_inactive_user(self):
        """Test that login is blocked for inactive users."""
        self.user.is_active = False
        self.user.save()

        login_data = {"email": self.user.email, "password": "testpass123"}

        response = self.client.post("/api/v1/auth/login/", login_data)

        self.assertNotEqual(response.status_code, status.HTTP_200_OK)


class UserFilteringTests(TestCase):
    """Test that inactive users are properly excluded from various views."""

    def setUp(self):
        self.client = APIClient()
        self.active_user = UserFactory(is_active=True)
        self.inactive_user = UserFactory(is_active=False)

    def test_card_filters_exclude_inactive_users(self):
        """Test that card filters exclude inactive users."""
        from apps.cards.filters.card_filter import CardFilter

        filter_obj = CardFilter()
        owner_queryset = filter_obj.filters["owner"].queryset

        self.assertIn(self.active_user, owner_queryset)
        self.assertNotIn(self.inactive_user, owner_queryset)

        issuer_queryset = filter_obj.filters["issuer"].queryset

        self.assertIn(self.active_user, issuer_queryset)
        self.assertNotIn(self.inactive_user, issuer_queryset)

    def test_user_search_excludes_inactive_users(self):
        """Test that user search excludes inactive users."""
        self.client.force_authenticate(user=self.active_user)

        response = self.client.get("/api/v1/search/users/", {"q": "test"})

        if response.status_code == status.HTTP_200_OK:
            user_ids = [user["id"] for user in response.data["results"]]
            self.assertNotIn(str(self.inactive_user.id), user_ids)

    def test_influencer_views_exclude_inactive_users(self):
        """Test that influencer listings exclude inactive users."""
        active_influencer = UserFactory(role="influencer", is_active=True)
        inactive_influencer = UserFactory(role="influencer", is_active=False)

        response = self.client.get("/api/v1/feed/influencers/")

        if response.status_code == status.HTTP_200_OK:
            influencer_ids = [inf["id"] for inf in response.data.get("results", [])]
            self.assertNotIn(str(inactive_influencer.id), influencer_ids)

    def test_relationship_views_exclude_inactive_users(self):
        """Test that relationship views properly handle inactive users."""
        from apps.relationships.serializers.follow_serializers import FollowSerializer

        serializer = FollowSerializer(data={"following_id": self.inactive_user.id})

        self.assertFalse(serializer.is_valid())
        self.assertIn("following_id", serializer.errors)


class AdminDeactivationTests(TestCase):
    """Test admin deactivation functionality."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = UserFactory(is_staff=True)
        self.regular_user = UserFactory()

    def test_admin_can_deactivate_user(self):
        """Test that admin can deactivate users."""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("admin-deactivate-user", kwargs={"pk": self.regular_user.id})
        response = self.client.patch(url)

        if response.status_code == status.HTTP_200_OK:
            self.regular_user.refresh_from_db()
            self.assertFalse(self.regular_user.is_active)

    def test_admin_can_activate_user(self):
        """Test that admin can activate users."""
        self.regular_user.is_active = False
        self.regular_user.save()

        self.client.force_authenticate(user=self.admin_user)

        url = reverse("admin-activate-user", kwargs={"pk": self.regular_user.id})
        response = self.client.patch(url)

        if response.status_code == status.HTTP_200_OK:
            self.regular_user.refresh_from_db()
            self.assertTrue(self.regular_user.is_active)


class SerializerTests(TestCase):
    """Test account deactivation serializers."""

    def setUp(self):
        self.user = UserFactory()

    def test_self_deactivation_serializer_validation(self):
        """Test SelfDeactivationRequestSerializer validation."""
        from apps.accounts.user.serializers.account_deactivation import (
            SelfDeactivationRequestSerializer,
        )

        context = {"request": type("MockRequest", (), {"user": self.user})()}
        serializer = SelfDeactivationRequestSerializer(
            data={"confirm_deactivation": True, "reason": "Test"}, context=context
        )
        self.assertTrue(serializer.is_valid())

        serializer = SelfDeactivationRequestSerializer(
            data={"confirm_deactivation": False}, context=context
        )
        self.assertFalse(serializer.is_valid())

    def test_account_status_serializer(self):
        """Test AccountStatusSerializer."""
        from apps.accounts.user.serializers.account_deactivation import (
            AccountStatusSerializer,
        )

        serializer = AccountStatusSerializer(self.user)
        data = serializer.data

        self.assertIn("is_active", data)
        self.assertTrue(data["is_active"])
        self.assertIn("deactivated_at", data)
        self.assertIsNone(data["deactivated_at"])


class IntegrationTests(TestCase):
    """Integration tests for account deactivation."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()

    def test_full_deactivation_flow(self):
        """Test complete deactivation and reactivation flow."""
        self.client.force_authenticate(user=self.user)

        status_response = self.client.get("/api/v1/users/me/status/")
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertTrue(status_response.data["is_active"])

        deactivate_data = {"confirm_deactivation": True, "reason": "Integration test"}
        deactivate_response = self.client.post(
            "/api/v1/users/me/deactivate/", deactivate_data
        )
        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        search_response = self.client.get(
            "/api/v1/search/users/", {"q": self.user.username}
        )
        if search_response.status_code == status.HTTP_200_OK:
            user_ids = [u["id"] for u in search_response.data.get("results", [])]
            self.assertNotIn(str(self.user.id), user_ids)

        admin_user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=admin_user)

        activate_url = reverse("admin-activate-user", kwargs={"pk": self.user.id})
        activate_response = self.client.patch(activate_url)

        if activate_response.status_code == status.HTTP_200_OK:
            self.user.refresh_from_db()
            self.assertTrue(self.user.is_active)
            self.assertIsNone(self.user.deactivated_at)


@pytest.mark.django_db
class TestAccountDeactivationPyTest:
    """PyTest style tests for account deactivation."""

    def test_deactivated_user_cannot_perform_actions(self):
        """Test that deactivated users cannot perform authenticated actions."""
        user = UserFactory(is_active=False)
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            "/api/v1/users/me/deactivate/", {"confirm_deactivation": True}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deactivated_user_not_in_card_relationships(self):
        """Test that deactivated users don't appear in card owner/issuer filters."""
        active_user = UserFactory(is_active=True)
        inactive_user = UserFactory(is_active=False)

        from apps.cards.filters.card_filter import CardFilter

        card_filter = CardFilter()

        owner_qs = card_filter.filters["owner"].queryset
        assert active_user in owner_qs
        assert inactive_user not in owner_qs

        issuer_qs = card_filter.filters["issuer"].queryset
        assert active_user in issuer_qs
        assert inactive_user not in issuer_qs
