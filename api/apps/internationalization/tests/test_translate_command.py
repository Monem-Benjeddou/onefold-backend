"""Tests for the translate management command."""

import os
import tempfile
from io import StringIO
from unittest import mock

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.internationalization.services import TranslationManager


class TestTranslateCommand(TestCase):
    """Test the translate management command."""

    def setUp(self):
        """Set up test environment."""
        self.out = StringIO()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.locale_dir = os.path.join(self.temp_dir.name, "locale")
        self.ar_dir = os.path.join(self.locale_dir, "ar", "LC_MESSAGES")
        os.makedirs(self.ar_dir, exist_ok=True)

        self.po_file_path = os.path.join(self.ar_dir, "django.po")
        with open(self.po_file_path, "w") as f:
            f.write(
                """
msgid ""
msgstr ""
"Project-Id-Version: Django\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2023-01-01 00:00+0000\\n"
"Language: ar\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

msgid "Hello, world!"
msgstr ""

msgid "Welcome"
msgstr ""
"""
            )

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    @mock.patch.object(TranslationManager, "translate_text")
    def test_translate_single_string(self, mock_translate):
        """Test translating a single string."""
        mock_translate.return_value = "مرحبا بالعالم!"

        call_command(
            "translate",
            "--string",
            "Hello, world!",
            "--languages",
            "ar",
            stdout=self.out,
        )

        output = self.out.getvalue()
        self.assertIn("Translation completed successfully", output)
        self.assertIn("مرحبا بالعالم!", output)
        mock_translate.assert_called_with(
            text="Hello, world!", dest_language="ar", source_language="en"
        )

    @mock.patch.object(TranslationManager, "translate_po_file")
    def test_translate_file(self, mock_translate_po_file):
        """Test translating a .po file."""
        mock_translate_po_file.return_value = {
            "total_entries": 2,
            "newly_translated": 2,
            "errors": 0,
        }

        call_command("translate", "--file", self.po_file_path, stdout=self.out)

        output = self.out.getvalue()
        self.assertIn("Translation completed successfully", output)
        self.assertIn("Total entries: 2", output)
        self.assertIn("Newly translated: 2", output)
        mock_translate_po_file.assert_called_once()

    @mock.patch.object(TranslationManager, "translate_all_po_files")
    def test_translate_all(self, mock_translate_all):
        """Test translating all .po files."""
        mock_translate_all.return_value = {
            "languages": ["ar"],
            "files_processed": 1,
            "files_with_errors": 0,
            "total_entries": 2,
            "newly_translated": 2,
            "language_stats": {
                "ar": {
                    "files_found": 1,
                    "files_processed": 1,
                    "total_entries": 2,
                    "newly_translated": 2,
                }
            },
        }

        call_command("translate", "--all", "--languages", "ar", stdout=self.out)

        output = self.out.getvalue()
        self.assertIn("Translation completed successfully", output)
        self.assertIn("Languages processed: 1", output)
        self.assertIn("Files processed: 1", output)
        mock_translate_all.assert_called_once()

    def test_list_languages(self):
        """Test listing available languages."""
        call_command("translate", "--list-languages", stdout=self.out)

        output = self.out.getvalue()
        self.assertIn("Available languages", output)

    def test_command_error_handling(self):
        """Test error handling in the command."""
        with self.assertRaises(CommandError):
            call_command("translate", "--file", "nonexistent.po", stdout=self.out)
