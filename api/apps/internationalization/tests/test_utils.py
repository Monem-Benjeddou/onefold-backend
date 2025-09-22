"""Tests for the internationalization utils."""

import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.internationalization.utils import (
    get_po_translated_string,
    extract_translatable_strings,
)


class GetPoTranslatedStringTests(TestCase):
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.locale_dir = os.path.join(self.temp_dir, "locale")
        self.ar_messages_dir = os.path.join(self.locale_dir, "ar", "LC_MESSAGES")
        os.makedirs(self.ar_messages_dir)

        self.po_file_path = os.path.join(self.ar_messages_dir, "django.po")
        with open(self.po_file_path, "w", encoding="utf-8") as f:
            f.write(
                """msgid "Hello"
msgstr "مرحبا"

msgid "Hello\\nWorld"
msgstr "مرحبا\\nالعالم"
"""
            )

        self.patcher = patch("django.conf.settings.LOCALE_PATHS", [self.locale_dir])
        self.mock_locale_paths = self.patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_get_po_translated_string_file_not_found(self):
        """Test getting translation when PO file doesn't exist."""

        os.remove(self.po_file_path)

        result = get_po_translated_string("Hello", "ar")
        self.assertEqual(result, "Hello")

        result = get_po_translated_string("Hello", "ar", test_mode=True)
        self.assertIsNone(result)

    def test_get_po_translated_string_found(self):
        """Test getting translation when string exists in PO file."""
        result = get_po_translated_string("Hello", "ar")
        self.assertEqual(result, "مرحبا")

    def test_get_po_translated_string_not_found(self):
        """Test getting translation when string doesn't exist in PO file."""
        result = get_po_translated_string("Goodbye", "ar")
        self.assertEqual(result, "Goodbye")

        result = get_po_translated_string("Goodbye", "ar", test_mode=True)
        self.assertIsNone(result)

    def test_get_po_translated_string_multiline(self):
        """Test getting translation for multi-line strings."""
        result = get_po_translated_string("Hello\nWorld", "ar")
        self.assertEqual(result, "مرحباالعالم")

    @patch("apps.internationalization.utils.polib.pofile")
    def test_get_po_translated_string_error(self, mock_pofile):
        """Test getting translation when an error occurs."""
        mock_pofile.side_effect = Exception("Test error")

        result = get_po_translated_string("Hello", "ar")
        self.assertEqual(result, "Hello")

        result = get_po_translated_string("Hello", "ar", test_mode=True)
        self.assertIsNone(result)


class ExtractTranslatableStringsTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_extract_translatable_strings_file_not_found(self):
        """Test extracting strings from non-existent file."""
        result = extract_translatable_strings("nonexistent.py")
        self.assertEqual(result, [])

    def test_extract_translatable_strings_syntax_error(self):
        """Test extracting strings from file with syntax error."""
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write("def invalid_syntax:")

        result = extract_translatable_strings(test_file)
        self.assertEqual(result, [])

    def test_extract_translatable_strings_simple(self):
        """Test extracting simple translatable strings."""
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write(
                """
from django.utils.translation import gettext_lazy as _

def test():
    message = _("Hello")
    error = _("Error occurred")
"""
            )

        result = extract_translatable_strings(test_file)
        self.assertEqual(set(result), {"Hello", "Error occurred"})

    def test_extract_translatable_strings_complex(self):
        """Test extracting complex translatable strings."""
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write(
                """
from django.utils.translation import gettext_lazy as _

class Test:
    TITLE = _("Test Title")
    
    def method(self):
        messages = [
            _("First message"),
            _("Second message")
        ]
        return {
            "error": _("Error message"),
            "success": _("Success message")
        }
"""
            )

        result = extract_translatable_strings(test_file)
        self.assertEqual(
            set(result),
            {
                "Test Title",
                "First message",
                "Second message",
                "Error message",
                "Success message",
            },
        )
