from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@override_settings(RATE_LIMITER_ENABLED=False)
class ExportTests(TestCase):
    """Tests for the export functionality"""

    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            username="admin",
            role="admin",
        )

        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="userpass123",
            username="user",
            role="user",
        )

        self.client.force_authenticate(user=self.admin_user)

    def test_export_users_csv(self):
        """Test exporting users in CSV format"""
        response = self.client.get("/api/v1/users/export/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_export_users_json(self):
        """Test exporting users in JSON format"""
        response = self.client.get("/api/v1/users/export/?format=json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_export_users_unauthorized(self):
        """Test that unauthorized users cannot export"""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get("/api/v1/users/export/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_users_unauthenticated(self):
        """Test that unauthenticated users cannot export"""
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/v1/users/export/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
