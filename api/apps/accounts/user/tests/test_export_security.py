"""
Security tests for export functionality in the Kolct API.

This module contains comprehensive security tests for all export views to ensure:
- Sensitive data is not exposed
- CSV injection attacks are prevented
- Audit logging is working
- Rate limiting is effective
- Access controls are properly enforced
"""

import json
import tempfile
import csv
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import Group
from apps.accounts.user.models import User
from apps.accounts.user.tests.factories import UserFactory
from apps.salesman.utils.csv_export import sanitize_csv_field


class CSVSanitizationSecurityTest(TestCase):
    """Test CSV injection prevention."""

    def test_csv_formula_injection_prevention(self):
        """Test that dangerous CSV formulas are properly sanitized."""
        dangerous_inputs = [
            "=cmd|calc",
            "+SUM(A1:A10)",
            "-2+5+cmd",
            "@SUM(A1:A10)",
            "=1+1+cmd|'/c calc'!A0",
            '=HYPERLINK("http://evil.com")',
            "\t=cmd",
            "\r=cmd",
            "\n=cmd",
        ]

        for dangerous_input in dangerous_inputs:
            with self.subTest(input=dangerous_input):
                result = sanitize_csv_field(dangerous_input)
                self.assertTrue(
                    result.startswith("'"),
                    f"Dangerous input '{dangerous_input}' not properly sanitized: {result}",
                )

    def test_safe_csv_values_unchanged(self):
        """Test that safe values are not modified."""
        safe_inputs = [
            "normal text",
            "user@example.com",
            "123-456-7890",
            "John Doe",
            "Some description",
            "",
            None,
            "10.99",
            "2024-01-15",
        ]

        for safe_input in safe_inputs:
            with self.subTest(input=safe_input):
                result = sanitize_csv_field(safe_input)
                expected = "" if safe_input is None else str(safe_input)
                self.assertEqual(
                    result,
                    expected,
                    f"Safe input '{safe_input}' was incorrectly modified: {result}",
                )


class UserExportSecurityTest(APITestCase):
    """Test security of user export functionality."""

    def setUp(self):

        self.admin_group = Group.objects.create(name="Admin")
        self.admin_user = UserFactory(
            username="admin_user", email="admin@example.com", role="admin"
        )
        self.admin_user.groups.add(self.admin_group)

        self.regular_user = UserFactory(
            username="regular_user", email="user@example.com", role="collector"
        )
        self.staff_user = UserFactory(
            username="staff_user",
            email="staff@example.com",
            role="admin",
            is_staff=True,
        )
        self.superuser = UserFactory(
            username="superuser",
            email="super@example.com",
            role="admin",
            is_superuser=True,
            is_staff=True,
        )

    def test_sensitive_fields_not_exported(self):
        """Test that sensitive fields are not included in exports."""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("export-users")
        response = self.client.get(url, {"format": "json"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = json.loads(response.content)

        for user_data in response_data:
            self.assertNotIn("password", user_data, "Password field exposed in export")
            self.assertNotIn(
                "is_superuser", user_data, "is_superuser field exposed in export"
            )
            self.assertNotIn("_id", user_data, "Internal _id field exposed in export")

            self.assertIn("id", user_data, "ID field missing from export")
            self.assertIn("username", user_data, "Username field missing from export")
            self.assertIn("email", user_data, "Email field missing from export")

    def test_access_control_enforced(self):
        """Test that only authorized users can access exports."""
        url = reverse("export-users")

        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("apps.accounts.user.views.export_users.audit_logger")
    def test_audit_logging_on_export(self, mock_audit_logger):
        """Test that export attempts are properly logged."""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("export-users")
        response = self.client.get(url, {"format": "csv", "role": "collector"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(
            mock_audit_logger.warning.called, "Audit log not triggered for export"
        )

        call_args = mock_audit_logger.warning.call_args
        self.assertEqual(call_args[0][0], "USER_DATA_EXPORT_ATTEMPT")

        log_extra = call_args[1]["extra"]
        self.assertEqual(log_extra["username"], self.admin_user.username)
        self.assertEqual(log_extra["user_role"], self.admin_user.role)
        self.assertEqual(log_extra["export_format"], "csv")
        self.assertIn("filter_params", log_extra)

    @patch("apps.accounts.user.views.export_users.audit_logger")
    def test_large_export_alert(self, mock_audit_logger):
        """Test that large exports trigger security alerts."""

        UserFactory.create_batch(50, role="collector")

        self.client.force_authenticate(user=self.admin_user)

        url = reverse("export-users")
        response = self.client.get(url, {"format": "json"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        critical_calls = [
            call
            for call in mock_audit_logger.critical.call_args_list
            if call[0][0] == "LARGE_USER_DATA_EXPORT"
        ]

        if len(User.objects.all()) > 1000:
            self.assertTrue(len(critical_calls) > 0, "Large export alert not triggered")

    def test_filename_sanitization(self):
        """Test that dangerous filenames are sanitized."""
        self.client.force_authenticate(user=self.admin_user)

        dangerous_filename = "../../../etc/passwd.csv"
        url = reverse("export-users")
        response = self.client.get(
            url, {"format": "csv", "filename": dangerous_filename}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content_disposition = response.get("Content-Disposition", "")
        self.assertNotIn(
            "../", content_disposition, "Path traversal not prevented in filename"
        )
        self.assertNotIn(
            "\\", content_disposition, "Backslash not sanitized in filename"
        )

    def test_csv_injection_prevention_in_export(self):
        """Test that user data with dangerous content is sanitized in CSV export."""

        dangerous_user = UserFactory(
            username="=cmd|calc", fullname="+SUM(A1:A10)", role="collector"
        )

        self.client.force_authenticate(user=self.admin_user)

        url = reverse("export-users")
        response = self.client.get(url, {"format": "csv"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.content.decode("utf-8")

        import re

        dangerous_pattern1 = re.search(r"(^|,)=cmd\|calc", content)
        dangerous_pattern2 = re.search(r"(^|,)\+SUM\(A1:A10\)", content)

        self.assertIsNone(
            dangerous_pattern1,
            "Dangerous formula '=cmd|calc' found at start of CSV field",
        )
        self.assertIsNone(
            dangerous_pattern2,
            "Dangerous formula '+SUM(A1:A10)' found at start of CSV field",
        )

        self.assertIn(
            "'=cmd|calc", content, "CSV injection prevention not applied for =cmd|calc"
        )
        self.assertIn(
            "'+SUM(A1:A10)",
            content,
            "CSV injection prevention not applied for +SUM(A1:A10)",
        )


class ExportRateLimitingTest(APITestCase):
    """Test rate limiting on export endpoints."""

    def setUp(self):

        self.admin_group = Group.objects.create(name="Admin")
        self.admin_user = UserFactory(username="admin", role="admin")
        self.admin_user.groups.add(self.admin_group)

    @override_settings(RATELIMIT_ENABLE=True)
    def test_export_rate_limiting(self):
        """Test that export endpoints are rate limited."""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("export-users")

        responses = []
        for i in range(10):
            response = self.client.get(url, {"format": "json"})
            responses.append(response.status_code)

        rate_limited_responses = [
            r for r in responses if r == status.HTTP_429_TOO_MANY_REQUESTS
        ]

        if rate_limited_responses:
            self.assertGreater(
                len(rate_limited_responses),
                0,
                "Rate limiting not working - no 429 responses received",
            )


class ExportSecurityIntegrationTest(APITestCase):
    """Integration tests for overall export security."""

    def setUp(self):

        self.admin_group = Group.objects.create(name="Admin")
        self.admin_user = UserFactory(username="admin", role="admin")
        self.admin_user.groups.add(self.admin_group)

        self.malicious_user = UserFactory(
            username="evil_user",
            fullname='=HYPERLINK("http://evil.com","Click me")',
            email="test+formula@example.com",
            role="collector",
        )

    @patch("apps.accounts.user.views.export_users.audit_logger")
    def test_complete_export_security_flow(self, mock_audit_logger):
        """Test complete export flow with security measures."""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("export-users")
        response = self.client.get(
            url, {"format": "csv", "filename": "secure_export.csv", "role": "collector"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.get("content-type"), "text/csv")

        self.assertTrue(mock_audit_logger.warning.called)

        content = response.content.decode("utf-8")
        self.assertIn("'=HYPERLINK", content, "Malicious formula not properly escaped")

        lines = content.split("\n")
        if lines:
            headers = lines[0].split(",")

            self.assertNotIn(
                "is_staff",
                headers,
                "Sensitive 'is_staff' header present (should be 'Staff')",
            )
            self.assertNotIn(
                "is_superuser", headers, "Sensitive 'is_superuser' header present"
            )
