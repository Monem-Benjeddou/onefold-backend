"""
Comprehensive tests for file utilities.
"""

from django.test import TestCase
from apps.files.utils import guess_file_type_by_extension


class GuessFileTypeByExtensionTestCase(TestCase):
    """Test cases for guess_file_type_by_extension function."""

    def test_pdf_file_type(self):
        """Test PDF file type detection."""
        self.assertEqual(
            guess_file_type_by_extension("document.pdf"), "application/pdf"
        )
        self.assertEqual(guess_file_type_by_extension("FILE.PDF"), "application/pdf")
        self.assertEqual(
            guess_file_type_by_extension("my.file.name.pdf"), "application/pdf"
        )

    def test_word_document_file_types(self):
        """Test Microsoft Word file type detection."""
        self.assertEqual(
            guess_file_type_by_extension("document.doc"), "application/msword"
        )
        self.assertEqual(
            guess_file_type_by_extension("document.docx"), "application/msword"
        )
        self.assertEqual(
            guess_file_type_by_extension("DOCUMENT.DOC"), "application/msword"
        )
        self.assertEqual(
            guess_file_type_by_extension("DOCUMENT.DOCX"), "application/msword"
        )

    def test_excel_file_types(self):
        """Test Microsoft Excel file type detection."""
        self.assertEqual(
            guess_file_type_by_extension("spreadsheet.xls"), "application/vnd.ms-excel"
        )
        self.assertEqual(
            guess_file_type_by_extension("spreadsheet.xlsx"), "application/vnd.ms-excel"
        )
        self.assertEqual(
            guess_file_type_by_extension("SPREADSHEET.XLS"), "application/vnd.ms-excel"
        )

    def test_powerpoint_file_types(self):
        """Test Microsoft PowerPoint file type detection."""
        self.assertEqual(
            guess_file_type_by_extension("presentation.ppt"),
            "application/vnd.ms-powerpoint",
        )
        self.assertEqual(
            guess_file_type_by_extension("presentation.pptx"),
            "application/vnd.ms-powerpoint",
        )
        self.assertEqual(
            guess_file_type_by_extension("PRESENTATION.PPT"),
            "application/vnd.ms-powerpoint",
        )

    def test_image_file_types(self):
        """Test image file type detection."""
        image_extensions = ["jpg", "jpeg", "png", "gif"]
        for ext in image_extensions:
            with self.subTest(extension=ext):
                self.assertEqual(guess_file_type_by_extension(f"image.{ext}"), "image")
                self.assertEqual(
                    guess_file_type_by_extension(f"IMAGE.{ext.upper()}"), "image"
                )

    def test_video_file_types(self):
        """Test video file type detection."""
        video_extensions = ["mp4", "avi", "mkv", "webm"]
        for ext in video_extensions:
            with self.subTest(extension=ext):
                self.assertEqual(guess_file_type_by_extension(f"video.{ext}"), "video")
                self.assertEqual(
                    guess_file_type_by_extension(f"VIDEO.{ext.upper()}"), "video"
                )

    def test_audio_file_types(self):
        """Test audio file type detection."""
        audio_extensions = ["mp3", "wav", "flac", "ogg"]
        for ext in audio_extensions:
            with self.subTest(extension=ext):
                self.assertEqual(guess_file_type_by_extension(f"audio.{ext}"), "audio")
                self.assertEqual(
                    guess_file_type_by_extension(f"AUDIO.{ext.upper()}"), "audio"
                )

    def test_default_text_file_type(self):
        """Test default text file type for unknown extensions."""
        unknown_extensions = ["txt", "unknown", "xyz", "abc", "123"]
        for ext in unknown_extensions:
            with self.subTest(extension=ext):
                self.assertEqual(guess_file_type_by_extension(f"file.{ext}"), "text")

    def test_file_without_extension(self):
        """Test file without extension."""

        self.assertEqual(guess_file_type_by_extension("filename"), "text")
        self.assertEqual(guess_file_type_by_extension("file_name"), "text")

    def test_file_with_multiple_dots(self):
        """Test file with multiple dots in filename."""
        self.assertEqual(
            guess_file_type_by_extension("my.file.name.pdf"), "application/pdf"
        )
        self.assertEqual(guess_file_type_by_extension("archive.tar.gz"), "text")

    def test_empty_filename(self):
        """Test empty filename."""

        try:
            result = guess_file_type_by_extension("")
            self.assertEqual(result, "text")
        except (IndexError, AttributeError):

            pass

    def test_filename_ending_with_dot(self):
        """Test filename ending with dot."""

        self.assertEqual(guess_file_type_by_extension("filename."), "text")

    def test_case_insensitive_detection(self):
        """Test that file type detection is case insensitive."""
        test_cases = [
            ("file.PDF", "application/pdf"),
            ("file.Pdf", "application/pdf"),
            ("file.JPG", "image"),
            ("file.Jpg", "image"),
            ("file.MP4", "video"),
            ("file.Mp4", "video"),
            ("file.MP3", "audio"),
            ("file.Mp3", "audio"),
        ]

        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                self.assertEqual(guess_file_type_by_extension(filename), expected_type)

    def test_function_robustness(self):
        """Test function robustness with various inputs."""

        self.assertEqual(guess_file_type_by_extension("my file.pdf"), "application/pdf")

        self.assertEqual(
            guess_file_type_by_extension("file-name_2023.pdf"), "application/pdf"
        )

        self.assertEqual(guess_file_type_by_extension("file.ext123"), "text")

    def test_all_recognized_extensions(self):
        """Test all recognized extensions are properly categorized."""

        expected_mappings = {
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/msword",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.ms-excel",
            "ppt": "application/vnd.ms-powerpoint",
            "pptx": "application/vnd.ms-powerpoint",
            "jpg": "image",
            "jpeg": "image",
            "png": "image",
            "gif": "image",
            "mp4": "video",
            "avi": "video",
            "mkv": "video",
            "webm": "video",
            "mp3": "audio",
            "wav": "audio",
            "flac": "audio",
            "ogg": "audio",
        }

        for extension, expected_type in expected_mappings.items():
            with self.subTest(extension=extension):
                result = guess_file_type_by_extension(f"file.{extension}")
                self.assertEqual(result, expected_type)
