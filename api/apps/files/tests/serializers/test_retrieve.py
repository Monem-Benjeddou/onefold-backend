from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.files.serializers.retrieve import FileSerializer
from apps.files.models import File
from apps.files.tests.constants import TEST_FILE_CONTENT


class FileSerializerTests(TestCase):
    """Test cases for FileSerializer."""

    def setUp(self):
        """Set up test data."""

        self.pdf_file = SimpleUploadedFile(
            "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
        )
        self.pdf_instance = File.objects.create(file=self.pdf_file, name="test.pdf")

        self.image_file = SimpleUploadedFile(
            "test.jpg", TEST_FILE_CONTENT, content_type="image/jpeg"
        )
        self.image_instance = File.objects.create(file=self.image_file, name="test.jpg")

        self.doc_file = SimpleUploadedFile(
            "test.docx",
            TEST_FILE_CONTENT,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.doc_instance = File.objects.create(file=self.doc_file, name="test.docx")

    def test_serialization_includes_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = FileSerializer(self.pdf_instance)
        data = serializer.data

        expected_fields = ["id", "_id", "file", "type"]
        for field in expected_fields:
            self.assertIn(field, data, f"Field {field} should be in serialized data")

        self.assertEqual(set(data.keys()), set(expected_fields))

    def test_pdf_file_type_detection(self):
        """Test file type detection for PDF files."""
        serializer = FileSerializer(self.pdf_instance)
        data = serializer.data

        self.assertEqual(data["type"], "application/pdf")

    def test_image_file_type_detection(self):
        """Test file type detection for image files."""
        serializer = FileSerializer(self.image_instance)
        data = serializer.data

        self.assertEqual(data["type"], "image")

    def test_document_file_type_detection(self):
        """Test file type detection for document files."""
        serializer = FileSerializer(self.doc_instance)
        data = serializer.data

        self.assertEqual(data["type"], "application/msword")

    def test_file_url_generation(self):
        """Test that file URL is properly generated."""
        serializer = FileSerializer(self.pdf_instance)
        data = serializer.data

        self.assertIn("file", data)
        self.assertIsNotNone(data["file"])

        self.assertIn("files", data["file"])

    def test_read_only_fields(self):
        """Test that read-only fields cannot be modified."""
        original_data = {
            "id": self.pdf_instance.id,
            "file": "modified_file",
            "type": "modified_type",
        }

        serializer = FileSerializer(self.pdf_instance, data=original_data, partial=True)

        self.assertTrue(serializer.is_valid())

        if serializer.is_valid():
            updated_instance = serializer.save()

            self.assertEqual(updated_instance.file.name, self.pdf_instance.file.name)

    def test_serialization_with_multiple_instances(self):
        """Test serialization with multiple file instances."""
        files = [self.pdf_instance, self.image_instance, self.doc_instance]
        serializer = FileSerializer(files, many=True)
        data = serializer.data

        self.assertEqual(len(data), 3)

        for file_data in data:
            self.assertIn("id", file_data)
            self.assertIn("_id", file_data)
            self.assertIn("file", file_data)
            self.assertIn("type", file_data)
            self.assertEqual(set(file_data.keys()), {"id", "_id", "file", "type"})

    def test_file_type_for_unknown_extension(self):
        """Test file type detection for unknown extensions."""

        unknown_file = SimpleUploadedFile(
            "test.xyz", TEST_FILE_CONTENT, content_type="application/octet-stream"
        )
        unknown_instance = File.objects.create(file=unknown_file, name="test.xyz")

        serializer = FileSerializer(unknown_instance)
        data = serializer.data

        self.assertEqual(data["type"], "text")

    def test_serialization_no_timestamps(self):
        """Test that created and updated timestamps are not included."""
        serializer = FileSerializer(self.pdf_instance)
        data = serializer.data

        self.assertNotIn("created", data)
        self.assertNotIn("updated", data)
        self.assertNotIn("name", data)
        self.assertNotIn("url", data)
        self.assertNotIn("size", data)

    def test_file_field_representation(self):
        """Test that file field is properly represented."""
        serializer = FileSerializer(self.pdf_instance)
        data = serializer.data

        self.assertIn("file", data)

        self.assertIn("files", data["file"])

    def test_serializer_context_handling(self):
        """Test that serializer handles context properly."""

        context = {"request": None}
        serializer = FileSerializer(self.pdf_instance, context=context)
        data = serializer.data

        self.assertIn("file", data)
        self.assertIsNotNone(data["file"])
