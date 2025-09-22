import json
import csv
from io import StringIO
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.accounts.user.tests.constants import (
    EXPORT_USERS_URL,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    USER_EMAIL,
    USER_USERNAME,
    USER_PASSWORD,
)

User = get_user_model()


@override_settings(RATE_LIMITER_ENABLED=False)
class ExportUsersTests(TestCase):
    """Tests for the export users functionality"""

    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            email=ADMIN_EMAIL, password=ADMIN_PASSWORD, username=ADMIN_USERNAME
        )
        self.admin_user.role = "admin"
        self.admin_user.save()

        self.regular_user = User.objects.create_user(
            email=USER_EMAIL, password=USER_PASSWORD, username=USER_USERNAME
        )
        self.dev_admin_user = User.objects.create_user(
            email="dev_admin@example.com",
            password="devadminpassword123",
            username="devadminuser",
            role="admin",
        )
        self.neo_admin_user = User.objects.create_user(
            email="neo_admin@example.com",
            password="neoadminpassword123",
            username="neoadminuser",
            role="admin",
        )

        self.client.force_authenticate(user=self.admin_user)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_csv_format(self):
        """Test exporting users in CSV format"""
        response = self.client.get(EXPORT_USERS_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        self.assertGreater(len(rows), 1)

        header = rows[0]
        expected_headers = [
            "ID",
            "Username",
            "Email",
            "Full Name",
            "Role",
            "Staff",
            "Created At",
            "Phone Number",
        ]
        self.assertEqual(header, expected_headers)

        emails = [row[2] for row in rows[1:]]
        self.assertIn(USER_EMAIL, emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_json_format(self):
        """Test exporting users in JSON format"""
        response = self.client.get(f"{EXPORT_USERS_URL}?format=json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        content = response.content.decode("utf-8")
        data = json.loads(content)

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        if data:
            user = data[0]
            expected_fields = [
                "id",
                "username",
                "email",
                "fullname",
                "role",
                "is_staff",
                "created_at",
                "phone_number",
            ]
            for field in expected_fields:
                self.assertIn(field, user)

        emails = [user["email"] for user in data]
        self.assertIn(USER_EMAIL, emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_with_role_filter(self):
        """Test exporting users with role filter"""
        response = self.client.get(f"{EXPORT_USERS_URL}?role=admin")

        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        emails = [row[2] for row in rows[1:]]
        self.assertEqual(len(emails), 2)
        self.assertIn("dev_admin@example.com", emails)
        self.assertNotIn(USER_EMAIL, emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_with_search_filter(self):
        """Test exporting users with search filter"""
        response = self.client.get(f"{EXPORT_USERS_URL}?search=neo_admin@example.com")

        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        emails = [row[2] for row in rows[1:]]
        self.assertEqual(len(emails), 1)
        self.assertIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        response = self.client.get(EXPORT_USERS_URL)

        self.assertEqual(response.status_code, 401)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_as_regular_user(self):
        """Test that regular users cannot export users"""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(EXPORT_USERS_URL)

        self.assertEqual(response.status_code, 403)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_rate_limit(self):
        """Test that export users endpoint is rate limited when enabled"""
        with self.settings(RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True):

            for i in range(4):
                response = self.client.get(EXPORT_USERS_URL)
                if i < 3:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 429)
