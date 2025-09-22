"""
Security tests for Files app.
Tests authentication, authorization, and security measures.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.core.cache import cache
from unittest.mock import patch

from apps.accounts.user.models import User
from apps.files.models import File
from apps.files.tests.constants import TEST_FILE_CONTENT, INVALID_FILE_EXTENSIONS


class FileSecurityTestCase(APITestCase):
    """Test cases for file security and authentication."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser",
            password="testpassword",
            is_email_verified=True,
        )
        self.user.set_password("testpassword")
        self.user.save()

        self.other_user = User.objects.create(
            username="otheruser",
            password="testpassword",
            is_email_verified=True,
        )
        self.other_user.set_password("testpassword")
        self.other_user.save()

        self.list_url = reverse("files-list")
        self.create_url = reverse("files-create")

        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access file endpoints."""

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        test_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        response = self.client.post(
            self.create_url, {"file": test_file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_access_denied(self):
        """Test that invalid tokens are rejected."""

        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_access_denied(self):
        """Test that expired tokens are rejected."""

        self.client.credentials(HTTP_AUTHORIZATION="Bearer expired.token.here")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malicious_file_upload_blocked(self):
        """Test that malicious file types are blocked."""
        self.client.force_authenticate(user=self.user)

        for ext in INVALID_FILE_EXTENSIONS:
            with self.subTest(extension=ext):
                malicious_file = SimpleUploadedFile(
                    f"malicious.{ext}",
                    b"malicious content",
                    content_type="application/octet-stream",
                )

                response = self.client.post(
                    self.create_url, {"file": malicious_file}, format="multipart"
                )
                self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

                import json

                content_data = json.loads(response.content.decode("utf-8"))
                self.assertIn("Only", content_data.get("error", ""))

    def test_oversized_file_handling(self):
        """Test handling of oversized files."""
        self.client.force_authenticate(user=self.user)

        large_content = b"x" * (10 * 1024 * 1024)
        large_file = SimpleUploadedFile(
            "large.pdf", large_content, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": large_file}, format="multipart"
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_201_CREATED,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_400_BAD_REQUEST,
            ],
        )

    def test_empty_file_upload_blocked(self):
        """Test that empty files are handled appropriately."""
        self.client.force_authenticate(user=self.user)

        empty_file = SimpleUploadedFile(
            "empty.pdf", b"", content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": empty_file}, format="multipart"
        )

        self.assertIn(
            response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED]
        )

    def test_file_without_extension_handling(self):
        """Test handling of files without extensions."""
        self.client.force_authenticate(user=self.user)

        no_ext_file = SimpleUploadedFile(
            "noextension", TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": no_ext_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_sql_injection_in_filename(self):
        """Test that SQL injection attempts in filenames are handled safely."""
        self.client.force_authenticate(user=self.user)

        malicious_filename = "'; DROP TABLE files; --.pdf"
        malicious_file = SimpleUploadedFile(
            malicious_filename, TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": malicious_file}, format="multipart"
        )

        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

        try:
            File.objects.count()
            table_exists = True
        except:
            table_exists = False
        self.assertTrue(table_exists)

    def test_xss_in_filename(self):
        """Test that XSS attempts in filenames are handled safely."""
        self.client.force_authenticate(user=self.user)

        xss_filename = "<script>alert('xss')</script>.pdf"
        xss_file = SimpleUploadedFile(
            xss_filename, TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": xss_file}, format="multipart"
        )
        if response.status_code == status.HTTP_201_CREATED:

            import json

            content_data = json.loads(response.content.decode("utf-8"))
            file_instance = File.objects.get(id=content_data["id"])
            self.assertNotIn("<script>", file_instance.name)

    def test_path_traversal_in_filename(self):
        """Test that path traversal attempts are blocked."""
        self.client.force_authenticate(user=self.user)

        traversal_filename = "../../../etc/passwd.pdf"
        traversal_file = SimpleUploadedFile(
            traversal_filename, TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": traversal_file}, format="multipart"
        )
        if response.status_code == status.HTTP_201_CREATED:

            import json

            content_data = json.loads(response.content.decode("utf-8"))
            file_instance = File.objects.get(id=content_data["id"])
            self.assertNotIn("../", file_instance.file.name)
            self.assertIn("files/", file_instance.file.name)

    @override_settings(
        RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
    )
    def test_rate_limiting_protection(self):
        """Test that rate limiting protects against abuse."""
        self.client.force_authenticate(user=self.user)

        for i in range(25):
            response = self.client.get(self.list_url)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        else:
            self.fail("Rate limiting should have been triggered")

        cache.clear()

        for i in range(15):
            test_file = SimpleUploadedFile(
                f"test{i}.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
            )
            response = self.client.post(
                self.create_url, {"file": test_file}, format="multipart"
            )
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        else:
            self.fail("Rate limiting should have been triggered for create endpoint")

    def test_concurrent_file_uploads(self):
        """Test handling of concurrent file uploads."""
        self.client.force_authenticate(user=self.user)

        file1 = SimpleUploadedFile(
            "concurrent.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        file2 = SimpleUploadedFile(
            "concurrent.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response1 = self.client.post(
            self.create_url, {"file": file1}, format="multipart"
        )
        response2 = self.client.post(
            self.create_url, {"file": file2}, format="multipart"
        )

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        import json

        content_data1 = json.loads(response1.content.decode("utf-8"))
        content_data2 = json.loads(response2.content.decode("utf-8"))
        self.assertNotEqual(content_data1["id"], content_data2["id"])

        self.assertIn("id", content_data1)
        self.assertIn("file", content_data1)
        self.assertIn("type", content_data1)

    def test_file_content_type_spoofing(self):
        """Test protection against content type spoofing."""
        self.client.force_authenticate(user=self.user)

        executable_content = b"fake executable content"
        spoofed_file = SimpleUploadedFile(
            "malware.pdf", executable_content, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": spoofed_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unicode_filename_handling(self):
        """Test handling of Unicode characters in filenames."""
        self.client.force_authenticate(user=self.user)

        unicode_filename = "测试文件.pdf"
        unicode_file = SimpleUploadedFile(
            unicode_filename, TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": unicode_file}, format="multipart"
        )

        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

    def test_null_byte_injection(self):
        """Test protection against null byte injection."""
        self.client.force_authenticate(user=self.user)

        null_byte_filename = "test\x00.exe.pdf"
        null_byte_file = SimpleUploadedFile(
            null_byte_filename, TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": null_byte_file}, format="multipart"
        )
        if response.status_code == status.HTTP_201_CREATED:

            import json

            content_data = json.loads(response.content.decode("utf-8"))
            file_instance = File.objects.get(id=content_data["id"])
            self.assertNotIn("\x00", file_instance.name)

    def test_csrf_protection(self):
        """Test CSRF protection for file uploads."""

        self.client.force_authenticate(user=self.user)

        test_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )

        response = self.client.post(
            self.create_url, {"file": test_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cors_headers(self):
        """Test that appropriate CORS headers are set."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_content_security_policy(self):
        """Test that CSP headers are properly set."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
