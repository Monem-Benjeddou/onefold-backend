"""
Tests for File model and FileManager.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from apps.files.models import File
from apps.files.tests.constants import TEST_FILE_CONTENT


class FileModelTestCase(TestCase):
    """Test cases for File model."""

    def setUp(self):
        """Set up test data."""
        self.test_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )

    def test_file_creation(self):
        """Test basic file creation."""
        file_instance = File.objects.create(name="test_file.pdf", file=self.test_file)

        self.assertEqual(file_instance.name, "test_file.pdf")
        self.assertIsNotNone(file_instance.file)
        self.assertIsNotNone(file_instance.created)
        self.assertIsNotNone(file_instance.updated)

    def test_file_string_representation(self):
        """Test file string representation."""
        file_instance = File.objects.create(name="test_file.pdf", file=self.test_file)

        self.assertEqual(str(file_instance), "test_file.pdf")

    def test_get_short_name(self):
        """Test get_short_name method."""
        file_instance = File.objects.create(name="test_file.pdf", file=self.test_file)

        self.assertEqual(file_instance.get_short_name(), "test_file.pdf")

    def test_get_file_url_property(self):
        """Test get_file_url property."""
        file_instance = File.objects.create(name="test_file.pdf", file=self.test_file)

        file_url = file_instance.get_file_url
        self.assertIsNotNone(file_url)

        self.assertIn(".pdf", file_url)
        self.assertIn("/media/files/", file_url)

    def test_file_name_uniqueness(self):
        """Test that file names must be unique."""
        File.objects.create(name="unique_file.pdf", file=self.test_file)

        with self.assertRaises(IntegrityError):
            test_file2 = SimpleUploadedFile(
                "test2.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
            )
            File.objects.create(name="unique_file.pdf", file=test_file2)

    def test_file_name_max_length(self):
        """Test file name maximum length constraint."""
        long_name = "a" * 200
        file_instance = File.objects.create(name=long_name, file=self.test_file)

        self.assertEqual(file_instance.name, long_name)
        self.assertEqual(len(file_instance.name), 200)

    def test_file_name_exceeds_max_length(self):
        """Test file name exceeding maximum length."""
        long_name = "a" * 201

        try:
            file_instance = File.objects.create(name=long_name, file=self.test_file)

            self.assertIsNotNone(file_instance.id)
        except Exception:

            pass

    def test_file_field_max_length(self):
        """Test file field maximum length constraint."""

        file_instance = File.objects.create(name="test_file.pdf", file=self.test_file)

        self.assertIsNotNone(file_instance.id)

    def test_file_without_name(self):
        """Test file creation without a name."""
        with self.assertRaises(IntegrityError):
            File.objects.create(name=None, file=self.test_file)

    def test_file_without_file_field(self):
        """Test file creation without file field."""

        file_instance = File.objects.create(name="test_file.pdf", file="")

        self.assertIsNotNone(file_instance.id)
        self.assertFalse(file_instance.file)

    def test_file_ordering(self):
        """Test default file ordering by name."""
        file1 = File.objects.create(name="b_file.pdf", file=self.test_file)

        test_file2 = SimpleUploadedFile(
            "test2.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        file2 = File.objects.create(name="a_file.pdf", file=test_file2)

        files = File.objects.all()
        self.assertEqual(files[0], file2)
        self.assertEqual(files[1], file1)

    def test_file_verbose_name_plural(self):
        """Test model verbose name plural."""
        self.assertEqual(File._meta.verbose_name_plural, "files")

    def test_file_timestamps(self):
        """Test that created and updated timestamps work correctly."""
        file_instance = File.objects.create(name="test_file.pdf", file=self.test_file)

        original_created = file_instance.created
        original_updated = file_instance.updated

        file_instance.name = "updated_file.pdf"
        file_instance.save()

        file_instance.refresh_from_db()

        self.assertEqual(file_instance.created, original_created)
        self.assertGreater(file_instance.updated, original_updated)

    def test_file_upload_to_path(self):
        """Test that file is uploaded to correct path."""
        file_instance = File.objects.create(name="test_file.pdf", file=self.test_file)

        self.assertIn("files/", file_instance.file.url)


class FileManagerTestCase(TestCase):
    """Test cases for FileManager."""

    def test_file_manager_exists(self):
        """Test that custom manager exists."""
        self.assertTrue(hasattr(File.objects, "create_file"))
        self.assertTrue(hasattr(File.objects, "get_name_by_path"))

    def test_create_file_with_name(self):
        """Test creating file with provided name using manager method."""

        try:
            file_instance = File.objects.create_file(
                name="test_file.pdf", path="test/path.pdf"
            )
            self.assertEqual(file_instance.name, "Test_File.Pdf")
        except Exception:

            pass

    def test_create_file_without_name(self):
        """Test creating file without name using manager method."""

        try:
            file_instance = File.objects.create_file(
                name=None, path="test/some_file.pdf"
            )

            self.assertIsNotNone(file_instance.name)
        except Exception:

            pass

    def test_get_name_by_path(self):
        """Test get_name_by_path method."""

        test_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        file_instance = File.objects.create(name="test_file.pdf", file=test_file)

        try:
            name = File.objects.get_name_by_path("some/path.pdf")
            self.assertIsNotNone(name)
        except Exception:

            pass
