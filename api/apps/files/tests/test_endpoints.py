from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.user.models import User
from apps.files.models import File
from apps.files.tests.constants import ALLOWED_FILE_EXTENSIONS
from core.utilities import tprint


class FileListCreateViewTests(APITestCase):
    """
    DEPRECATED: This test class is deprecated.
    Use test_create.py and test_list.py instead.
    Kept for backward compatibility.
    """

    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            password="testpassword",
            is_email_verified=True,
        )
        self.user.set_password("testpassword")
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.valid_file = SimpleUploadedFile(
            "file.pdf", b"file_content", content_type="application/pdf"
        )
        self.invalid_file = SimpleUploadedFile(
            "file.exe",
            b"file_content",
            content_type="application/x-msdownload",
        )

    def test_list_files_success(self):

        url = reverse("files-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_file_success(self):

        url = reverse("files-create")
        data = {"file": self.valid_file}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("type", response.data)

    def test_create_file_invalid_extension(self):

        url = reverse("files-create")
        data = {"file": self.invalid_file}
        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(
            response.json()["error"],
            f"Only {', '.join(ALLOWED_FILE_EXTENSIONS)} files are allowed",
        )
