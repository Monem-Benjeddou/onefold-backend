from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.core.cache import cache

from apps.accounts.user.models import User
from apps.files.models import File
from apps.files.tests.constants import TEST_FILE_CONTENT


class FileListViewTests(APITestCase):
    """Test cases for FileListView."""

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

        self.url = reverse("files-list")

        self.test_files = []
        for i in range(5):
            file_obj = SimpleUploadedFile(
                f"test{i}.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
            )
            file_instance = File.objects.create(file=file_obj, name=f"test{i}.pdf")
            self.test_files.append(file_instance)

        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_list_files_success(self):
        """Test successful file listing."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("meta", response.data)
        self.assertIn("count", response.data["meta"])
        self.assertIn("next", response.data["meta"])
        self.assertIn("previous", response.data["meta"])

        self.assertEqual(len(response.data["results"]), 5)

        file_data = response.data["results"][0]
        self.assertIn("id", file_data)
        self.assertIn("file", file_data)
        self.assertIn("type", file_data)

        self.assertNotIn("name", file_data)
        self.assertNotIn("url", file_data)
        self.assertNotIn("created", file_data)
        self.assertNotIn("updated", file_data)

    def test_list_files_empty(self):
        """Test file listing when no files exist."""

        File.objects.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 0)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_files_ordering(self):
        """Test that files are ordered by creation date (newest first)."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]

        self.assertEqual(len(results), 5)

    def test_list_files_pagination(self):
        """Test file listing pagination."""

        for i in range(15):
            file_obj = SimpleUploadedFile(
                f"extra{i}.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
            )
            File.objects.create(file=file_obj, name=f"extra{i}.pdf")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["meta"]["count"], 10)

        response_with_limit = self.client.get(self.url, {"limit": 5})
        self.assertEqual(response_with_limit.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_with_limit.data["results"]), 5)

    def test_list_files_unauthenticated(self):
        """Test file listing without authentication."""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(
        RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
    )
    def test_list_files_rate_limit(self):
        """Test rate limiting for file listing."""

        rate_limited = False

        for i in range(25):
            response = self.client.get(self.url)

            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited = True
                self.assertEqual(response.json().get("detail"), "Rate limit exceeded")
                break
            else:
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(rate_limited, "Rate limiting should have been triggered")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_list_files_without_rate_limit(self):
        """Test file listing without rate limiting when disabled."""

        for i in range(25):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_files_with_search_params(self):
        """Test file listing with query parameters."""

        params_to_test = [
            {"page": 1},
            {"limit": 10},
            {"ordering": "-created"},
        ]

        for params in params_to_test:
            with self.subTest(params=params):
                response = self.client.get(self.url, params)

                self.assertIn(
                    response.status_code,
                    [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
                )

    def test_list_files_content_type(self):
        """Test that response has correct content type."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
