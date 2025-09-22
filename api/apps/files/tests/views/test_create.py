from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.core.cache import cache

from apps.accounts.user.models import User
from apps.files.models import File
from apps.files.tests.constants import (
    ALLOWED_FILE_EXTENSIONS,
    INVALID_FILE_EXTENSIONS,
    TEST_FILE_CONTENT,
)


class FileCreateViewTests(APITestCase):
    """Test cases for FileCreateView."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser",
            password="testpassword",
            is_email_verified=True,
        )
        self.user.set_password("testpassword")
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"

        self.url = reverse("files-create")

        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_create_file_success(self):
        """Test successful file creation."""
        valid_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        data = {"file": valid_file}

        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("file", response.data)
        self.assertIn("type", response.data)

        self.assertNotIn("url", response.data)
        self.assertNotIn("name", response.data)
        self.assertNotIn("created", response.data)
        self.assertEqual(response.data["type"], "application/pdf")

        self.assertTrue(File.objects.filter(id=response.data["id"]).exists())

    def test_create_file_all_allowed_extensions(self):
        """Test file creation with all allowed extensions."""
        for extension in ALLOWED_FILE_EXTENSIONS:
            with self.subTest(extension=extension):
                valid_file = SimpleUploadedFile(
                    f"test.{extension}",
                    TEST_FILE_CONTENT,
                    content_type="application/octet-stream",
                )
                data = {"file": valid_file}

                response = self.client.post(self.url, data, format="multipart")

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertIn("id", response.data)
                self.assertIn("type", response.data)

    def test_create_file_invalid_extension(self):
        """Test file creation with invalid extensions."""
        for extension in INVALID_FILE_EXTENSIONS:
            with self.subTest(extension=extension):
                invalid_file = SimpleUploadedFile(
                    f"test.{extension}",
                    TEST_FILE_CONTENT,
                    content_type="application/octet-stream",
                )
                data = {"file": invalid_file}

                response = self.client.post(self.url, data, format="multipart")

                self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

                response_data = response.json()
                self.assertIn("error", response_data)

    def test_create_file_no_file(self):
        """Test file creation without providing a file."""
        data = {}

        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        self.assertIn("error", response_data)

    def test_create_file_empty_file(self):
        """Test file creation with empty file."""
        empty_file = SimpleUploadedFile("test.pdf", b"", content_type="application/pdf")
        data = {"file": empty_file}

        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn("error", response_data)

    def test_create_file_unauthenticated(self):
        """Test file creation without authentication."""
        self.client.force_authenticate(user=None)

        valid_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        data = {"file": valid_file}

        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(
        RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
    )
    def test_create_file_rate_limit(self):
        """Test rate limiting for file creation."""

        rate_limited = False

        for i in range(15):
            valid_file = SimpleUploadedFile(
                f"test{i}.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
            )
            data = {"file": valid_file}

            response = self.client.post(self.url, data, format="multipart")

            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited = True
                self.assertEqual(response.json().get("detail"), "Rate limit exceeded")
                break
            else:
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(rate_limited, "Rate limiting should have been triggered")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_create_file_without_rate_limit(self):
        """Test file creation without rate limiting when disabled."""

        for i in range(15):
            valid_file = SimpleUploadedFile(
                f"test{i}.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
            )
            data = {"file": valid_file}

            response = self.client.post(self.url, data, format="multipart")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
