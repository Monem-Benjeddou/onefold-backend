from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import NotAcceptable, ValidationError

from apps.files.serializers.create import CreateFileSerializer
from apps.files.models import File
from apps.files.tests.constants import (
    ALLOWED_FILE_EXTENSIONS,
    INVALID_FILE_EXTENSIONS,
    TEST_FILE_CONTENT,
)


class CreateFileSerializerTests(TestCase):
    """Test cases for CreateFileSerializer."""

    def test_valid_file_serialization(self):
        """Test serialization with valid file."""
        valid_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        data = {"file": valid_file}

        serializer = CreateFileSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_all_allowed_extensions(self):
        """Test serialization with all allowed file extensions."""
        for extension in ALLOWED_FILE_EXTENSIONS:
            with self.subTest(extension=extension):
                valid_file = SimpleUploadedFile(
                    f"test.{extension}",
                    TEST_FILE_CONTENT,
                    content_type="application/octet-stream",
                )
                data = {"file": valid_file}

                serializer = CreateFileSerializer(data=data)

                self.assertTrue(
                    serializer.is_valid(), f"Extension {extension} should be valid"
                )

    def test_invalid_extensions(self):
        """Test serialization with invalid file extensions."""
        for extension in INVALID_FILE_EXTENSIONS:
            with self.subTest(extension=extension):
                invalid_file = SimpleUploadedFile(
                    f"test.{extension}",
                    TEST_FILE_CONTENT,
                    content_type="application/octet-stream",
                )
                data = {"file": invalid_file}

                serializer = CreateFileSerializer(data=data)

                with self.assertRaises(NotAcceptable):
                    serializer.is_valid(raise_exception=True)

    def test_missing_file(self):
        """Test serialization without file."""
        data = {}

        serializer = CreateFileSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_empty_file(self):
        """Test serialization with empty file."""
        empty_file = SimpleUploadedFile("test.pdf", b"", content_type="application/pdf")
        data = {"file": empty_file}

        serializer = CreateFileSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_file_creation(self):
        """Test file creation through serializer."""
        valid_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        data = {"file": valid_file}

        serializer = CreateFileSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        file_instance = serializer.save()

        self.assertIsInstance(file_instance, File)
        self.assertTrue(file_instance.name.endswith(".pdf"))
        self.assertIn("-", file_instance.name)
        self.assertTrue(File.objects.filter(id=file_instance.id).exists())

    def test_file_name_generation(self):
        """Test that file names are generated with UUID."""
        valid_file = SimpleUploadedFile(
            "original_name.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        data = {"file": valid_file}

        serializer = CreateFileSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        file_instance = serializer.save()

        self.assertNotEqual(file_instance.name, "original_name.pdf")

        self.assertTrue(file_instance.name.endswith(".pdf"))

        self.assertIn("-", file_instance.name)

    def test_case_insensitive_extension(self):
        """Test that file extension validation is case insensitive."""

        valid_file = SimpleUploadedFile(
            "test.PDF", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        data = {"file": valid_file}

        serializer = CreateFileSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_multiple_dots_in_filename(self):
        """Test files with multiple dots in filename."""
        valid_file = SimpleUploadedFile(
            "test.file.with.dots.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        data = {"file": valid_file}

        serializer = CreateFileSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        file_instance = serializer.save()

        self.assertTrue(file_instance.name.endswith(".pdf"))

    def test_file_without_extension(self):
        """Test file without extension."""
        invalid_file = SimpleUploadedFile(
            "test_file_no_extension",
            TEST_FILE_CONTENT,
            content_type="application/octet-stream",
        )
        data = {"file": invalid_file}

        serializer = CreateFileSerializer(data=data)

        with self.assertRaises(NotAcceptable):
            serializer.is_valid(raise_exception=True)
