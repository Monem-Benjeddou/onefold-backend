import json
import csv
from io import StringIO
from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from apps.accounts.user.models import User


class ExportFiltersTests(TestCase):
    """Tests for the export users filters functionality"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("export-users")

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123", username="adminuser"
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
        response = self.client.get(f"{self.url}?role=admin")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 3)
        self.assertNotIn("admin@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)
        self.assertIn("staff@example.com", emails)
        self.assertNotIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_email_contains(self):
        """Test filtering users by email contains"""
        response = self.client.get(f"{self.url}?email=dev_admin")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("dev_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_email_exact(self):
        """Test filtering users by exact email"""
        response = self.client.get(f"{self.url}?email_exact=staff@example.com")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("staff@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_email_domain(self):
        """Test filtering users by email domain"""
        response = self.client.get(f"{self.url}?email_domain=gmail.com")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("user@gmail.com", emails)
        self.assertNotIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_is_active(self):
        """Test filtering users by active status based on last_login and created date"""
        response = self.client.get(f"{self.url}?is_active=false")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("inactive@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)
        self.assertNotIn("regular@example.com", emails)
        self.assertNotIn("dev_admin@example.com", emails)
        self.assertNotIn("staff@example.com", emails)
        self.assertNotIn("user@gmail.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_by_username(self):
        """Test filtering users by username"""
        response = self.client.get(f"{self.url}?username=staff")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("staff@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_exclude_staff(self):
        """Test filtering to exclude staff users"""
        response = self.client.get(f"{self.url}?exclude_staff=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertNotIn("staff@example.com", emails)
        self.assertIn("regular@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_inactive_only(self):
        """Test filtering to include only inactive users"""
        response = self.client.get(f"{self.url}?inactive_only=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("inactive@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)
        self.assertNotIn("regular@example.com", emails)
        self.assertNotIn("dev_admin@example.com", emails)
        self.assertNotIn("staff@example.com", emails)
        self.assertNotIn("user@gmail.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_never_logged_in(self):
        """Test filtering users who have never logged in"""
        response = self.client.get(f"{self.url}?never_logged_in=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("inactive@example.com", emails)
        self.assertIn("staff@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)
        self.assertIn("user@gmail.com", emails)

        self.assertNotIn("regular@example.com", emails)
        self.assertNotIn("dev_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_has_logged_in(self):
        """Test filtering users who have logged in"""
        response = self.client.get(f"{self.url}?has_logged_in=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("regular@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)

        self.assertNotIn("inactive@example.com", emails)
        self.assertNotIn("staff@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_multiple_roles(self):
        """Test filtering users by multiple roles"""
        response = self.client.get(f"{self.url}?role=user")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertIn("regular@example.com", emails)
        self.assertIn("inactive@example.com", emails)
        self.assertIn("user@gmail.com", emails)
        self.assertNotIn("dev_admin@example.com", emails)
        self.assertNotIn("neo_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_search(self):
        """Test filtering users by search term"""
        response = self.client.get(f"{self.url}?search=dev_admin")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("dev_admin@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_combination(self):
        """Test filtering users by a combination of filters"""

        response = self.client.get(f"{self.url}?role=user&never_logged_in=true")

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 2)
        self.assertIn("inactive@example.com", emails)
        self.assertIn("user@gmail.com", emails)
        self.assertNotIn("regular@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_json_format(self):
        """Test filtering users with JSON format"""
        response = self.client.get(f"{self.url}?format=json&role=admin")

        self.assertEqual(response.status_code, 200)
        data = self._parse_json_response(response)
        emails = self._get_emails_from_json(data)

        self.assertEqual(len(emails), 3)
        self.assertNotIn("admin@example.com", emails)
        self.assertIn("dev_admin@example.com", emails)
        self.assertIn("neo_admin@example.com", emails)
        self.assertIn("staff@example.com", emails)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_filter_complex_combination(self):
        """Test filtering users by a complex combination of filters"""

        response = self.client.get(
            f"{self.url}?has_logged_in=true&exclude_staff=true&email_domain=gmail.com"
        )

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 0)

        response = self.client.get(
            f"{self.url}?has_logged_in=true&exclude_staff=true&role=admin"
        )

        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv_response(response)
        emails = self._get_emails_from_csv(rows)

        self.assertEqual(len(emails), 1)
        self.assertIn("dev_admin@example.com", emails)
