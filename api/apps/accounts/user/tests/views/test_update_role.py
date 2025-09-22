from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from apps.accounts.user.models import User


@override_settings(RATE_LIMITER_ENABLED=False)
class UpdateRoleViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.user_to_update = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Password123",
            fullname="Test User Original",
            role="user",
        )

        self.url = reverse("update-role", kwargs={"pk": self.user_to_update.pk})

        self.client.force_authenticate(user=self.admin_user)

        self.valid_data = {
            "role": "admin",
        }

    def test_update_role_authenticated_as_admin(self):
        """Test updating a user role when authenticated as admin"""
        response = self.client.patch(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertEqual(response.data["status"], "Role updated to admin")

        self.user_to_update.refresh_from_db()
        self.assertEqual(self.user_to_update.role, self.valid_data["role"])

    def test_update_role_nonexistent_user(self):
        """Test updating role of a user that doesn't exist"""
        non_existent_url = reverse("update-role", kwargs={"pk": uuid.uuid4()})

        response = self.client.patch(non_existent_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_role_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        response = self.client.patch(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_role_as_regular_user(self):
        """Test that regular users cannot update roles"""
        regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="Password123",
            role="user",
        )
        self.client.force_authenticate(user=regular_user)

        response = self.client.patch(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
