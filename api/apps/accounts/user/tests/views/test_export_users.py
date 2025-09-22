import json
import csv
from io import StringIO
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.user.models import User


class ExportUsersTests(TestCase):
    """Tests for the export users functionality"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("export-users")

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123", username="adminuser"
        )

        self.regular_user = User.objects.create_user(
            email="testuser@example.com",
            password="userpass123",
            username="testuser",
            fullname="Test User",
        )

        self.dev_admin_user = User.objects.create_user(
            email="dev_admin@example.com",
            password="devadminpassword123",
            username="devadminuser",
            role="admin",
            fullname="Dev Admin User",
        )

        self.neo_admin_user = User.objects.create_user(
            email="neo_admin@example.com",
            password="neoadminpassword123",
            username="neoadminuser",
            role="moderator",
            fullname="Neo Admin User",
        )

        self.client.force_authenticate(user=self.admin_user)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_csv_format(self):
        """Test exporting users in CSV format"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertTrue(
            'attachment; filename="users' in response["Content-Disposition"]
        )

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        self.assertEqual(
            rows[0],
            [
                "ID",
                "Username",
                "Email",
                "Full Name",
                "Role",
                "Staff",
                "Created At",
                "Phone Number",
            ],
        )

        self.assertEqual(len(rows), 4)

        emails = [row[2] for row in rows[1:]]
        self.assertIn("testuser@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)

        self.assertNotIn("admin@example.com", emails)

        response = self.client.get(f"{self.url}?include_superusers=true")
        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        self.assertEqual(len(rows), 5)

        emails = [row[2] for row in rows[1:]]
        self.assertIn("admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_json_format(self):
        """Test exporting users in JSON format"""
        response = self.client.get(f"{self.url}?format=json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTrue(
            'attachment; filename="users' in response["Content-Disposition"]
        )

        content = response.content.decode("utf-8")
        users_data = json.loads(content)

        self.assertEqual(len(users_data), 3)

        emails = [user["email"] for user in users_data]
        self.assertIn("testuser@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)

        self.assertNotIn("admin@example.com", emails)

        response = self.client.get(f"{self.url}?format=json&include_superusers=true")
        content = response.content.decode("utf-8")
        users_data = json.loads(content)

        self.assertEqual(len(users_data), 4)

        emails = [user["email"] for user in users_data]
        self.assertIn("admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_filtered_by_role(self):
        """Test exporting users filtered by role"""
        response = self.client.get(f"{self.url}?role=admin")

        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        self.assertEqual(len(rows), 2)

        emails = [row[2] for row in rows[1:]]
        self.assertIn("dev_admin@example.com", emails)
        self.assertNotIn("admin@example.com", emails)
        self.assertNotIn("testuser@example.com", emails)
        self.assertNotIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_search_by_email(self):
        """Test exporting users filtered by search term"""
        response = self.client.get(f"{self.url}?search=neo_admin@example.com")

        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        self.assertEqual(len(rows), 2)

        emails = [row[2] for row in rows[1:]]
        self.assertIn("neo_admin@example.com", emails)
        self.assertNotIn("admin@example.com", emails)
        self.assertNotIn("testuser@example.com", emails)
        self.assertNotIn("dev_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_unauthorized(self):
        """Test that non-admin users cannot export users"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_unauthenticated(self):
        """Test that unauthenticated users cannot export users"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_rate_limit(self):
        """Test rate limiting for export users"""

        with self.settings(RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True):

            from django.core.cache import cache

            cache.clear()

            for i in range(3):
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.json().get("detail"), "Rate limit exceeded")
