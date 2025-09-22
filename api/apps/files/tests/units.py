from django.test import TestCase
from apps.files.utils import guess_file_type_by_extension


class UtilsTests(TestCase):
    def test_guess_file_type_by_extension(self):
        self.assertEqual(guess_file_type_by_extension("file.pdf"), "application/pdf")

        self.assertEqual(guess_file_type_by_extension("file.doc"), "application/msword")
        self.assertEqual(
            guess_file_type_by_extension("file.docx"), "application/msword"
        )

        self.assertEqual(
            guess_file_type_by_extension("file.xls"),
            "application/vnd.ms-excel",
        )
        self.assertEqual(
            guess_file_type_by_extension("file.xlsx"),
            "application/vnd.ms-excel",
        )

        self.assertEqual(
            guess_file_type_by_extension("file.ppt"),
            "application/vnd.ms-powerpoint",
        )
        self.assertEqual(
            guess_file_type_by_extension("file.pptx"),
            "application/vnd.ms-powerpoint",
        )

        self.assertEqual(guess_file_type_by_extension("file.jpg"), "image")
        self.assertEqual(guess_file_type_by_extension("file.jpeg"), "image")
        self.assertEqual(guess_file_type_by_extension("file.png"), "image")
        self.assertEqual(guess_file_type_by_extension("file.gif"), "image")

        self.assertEqual(guess_file_type_by_extension("file.mp4"), "video")
        self.assertEqual(guess_file_type_by_extension("file.avi"), "video")
        self.assertEqual(guess_file_type_by_extension("file.mkv"), "video")
        self.assertEqual(guess_file_type_by_extension("file.webm"), "video")

        self.assertEqual(guess_file_type_by_extension("file.mp3"), "audio")
        self.assertEqual(guess_file_type_by_extension("file.wav"), "audio")
        self.assertEqual(guess_file_type_by_extension("file.flac"), "audio")
        self.assertEqual(guess_file_type_by_extension("file.ogg"), "audio")

        self.assertEqual(guess_file_type_by_extension("file.txt"), "text")
