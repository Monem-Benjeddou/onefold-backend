import json
import csv
from io import StringIO
from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.user.tests.constants import (
    EXPORT_USERS_URL,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
)

User = get_user_model()


@override_settings(RATE_LIMITER_ENABLED=False)
class ExportFiltersTests(TestCase):
    """Tests for the export users filters functionality"""

    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            email=ADMIN_EMAIL, password=ADMIN_PASSWORD, username=ADMIN_USERNAME
        )
        self.admin_user.role = "admin"
        self.admin_user.save()

        self.regular_user = User.objects.create_user(
            email="regular@example.com",
            password="password123",
            username="regularuser",
            role="user",
        )

        self.regular_user.last_login = timezone.now()
        self.regular_user.save()

        self.dev_admin_user = User.objects.create_user(
            email="dev_admin@example.com",
            password="password123",
            username="devadminuser",
            role="admin",
        )

        self.dev_admin_user.last_login = timezone.now() - timedelta(days=10)
        self.dev_admin_user.save()

        self.neo_admin_user = User.objects.create_user(
            email="neo_admin@example.com",
            password="password123",
            username="neoadminuser",
            role="admin",
        )

        self.neo_admin_user.created = timezone.now() - timedelta(days=60)
        self.neo_admin_user.save()

        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            username="staffuser",
            role="admin",
            is_staff=True,
        )

        self.staff_user.save()

        self.inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="password123",
            username="inactiveuser",
            role="user",
        )

        self.inactive_user.created = timezone.now() - timedelta(days=60)
        self.inactive_user.save()

        self.gmail_user = User.objects.create_user(
            email="user@gmail.com",
            password="password123",
            username="gmailuser",
            role="user",
        )

        self.gmail_user.save()

        self.client.force_authenticate(user=self.admin_user)

    def _parse_csv_response(self, response):
        """Helper method to parse CSV response"""
        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        return list(csv_reader)

    def _parse_json_response(self, response):
        """Helper method to parse JSON response"""
        content = response.content.decode("utf-8")
        return json.loads(content)

    def _get_emails_from_csv(self, rows):
        """Helper method to extract emails from CSV rows"""

        return [row[2] for row in rows[1:]]

    def _get_emails_from_json(self, data):
        """Helper method to extract emails from JSON data"""
        return [user["email"] for user in data]

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_role(self):
        """Test filtering users by role"""
        response = self.client.get(f"{EXPORT_USERS_URL}?role=admin")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 3)
        self.assertIn("dev_admin@example.com", emails)
        self.assertNotIn("regular@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_email_domain(self):
        """Test filtering users by email domain"""
        response = self.client.get(f"{EXPORT_USERS_URL}?email_domain=gmail.com")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("user@gmail.com", emails)
        self.assertNotIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_email_exact(self):
        """Test filtering users by exact email"""
        response = self.client.get(
            f"{EXPORT_USERS_URL}?email_exact=regular@example.com"
        )

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_username(self):
        """Test filtering users by username"""
        response = self.client.get(f"{EXPORT_USERS_URL}?username=gmail")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("user@gmail.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_is_active_true(self):
        """Test filtering users by active status (true)"""
        response = self.client.get(f"{EXPORT_USERS_URL}?is_active=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("regular@example.com", emails)
        self.assertIn("user@gmail.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_is_active_false(self):
        """Test filtering users by active status (false)"""
        response = self.client.get(f"{EXPORT_USERS_URL}?is_active=false")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("neo_admin@example.com", emails)
        self.assertIn("inactive@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_exclude_staff(self):
        """Test excluding staff users"""
        response = self.client.get(f"{EXPORT_USERS_URL}?exclude_staff=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertNotIn("staff@example.com", emails)
        self.assertIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_inactive_only(self):
        """Test filtering for inactive users only"""
        response = self.client.get(f"{EXPORT_USERS_URL}?inactive_only=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("neo_admin@example.com", emails)
        self.assertIn("inactive@example.com", emails)
        self.assertNotIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_never_logged_in(self):
        """Test filtering users who never logged in"""
        response = self.client.get(f"{EXPORT_USERS_URL}?never_logged_in=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("neo_admin@example.com", emails)
        self.assertIn("staff@example.com", emails)
        self.assertIn("inactive@example.com", emails)
        self.assertIn("user@gmail.com", emails)
        self.assertNotIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_has_logged_in(self):
        """Test filtering users who have logged in"""
        response = self.client.get(f"{EXPORT_USERS_URL}?has_logged_in=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("regular@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertNotIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_multiple_role_filter(self):
        """Test filtering by multiple roles"""
        response = self.client.get(f"{EXPORT_USERS_URL}?role=user&role=admin")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertGreater(len(emails), 1)
        self.assertIn("regular@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_combined_filters_role_and_login_status(self):
        """Test combining role filter with login status"""
        response = self.client.get(f"{EXPORT_USERS_URL}?role=user&has_logged_in=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("regular@example.com", emails)
        self.assertNotIn("inactive@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_combined_filters_multiple_roles_and_login_status(self):
        """Test combining multiple role filters with login status"""
        response = self.client.get(
            f"{EXPORT_USERS_URL}?role=user&role=admin&has_logged_in=true"
        )

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("regular@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertNotIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_json_format_with_role_filter(self):
        """Test JSON export with role filter"""
        response = self.client.get(f"{EXPORT_USERS_URL}?role=user&format=json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = self._parse_json_response(response)
        emails = self._get_emails_from_json(data)

        self.assertIn("regular@example.com", emails)
        self.assertIn("inactive@example.com", emails)
        self.assertIn("user@gmail.com", emails)
        self.assertNotIn("dev_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_json_format_with_combined_filters(self):
        """Test JSON export with combined filters"""
        response = self.client.get(
            f"{EXPORT_USERS_URL}?role=user&exclude_staff=true&has_logged_in=true&format=json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = self._parse_json_response(response)
        emails = self._get_emails_from_json(data)

        self.assertIn("regular@example.com", emails)
        self.assertNotIn("staff@example.com", emails)
        self.assertNotIn("inactive@example.com", emails)
