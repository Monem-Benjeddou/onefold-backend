"""Tests for the translate management command."""

from io import StringIO
from django.test import TestCase
from django.core.management import call_command, CommandError
from unittest.mock import patch, MagicMock
from apps.internationalization.services import TranslationError


class TranslateCommandTests(TestCase):
    def setUp(self):
        self.out = StringIO()

    @patch("apps.internationalization.management.commands.translate.TranslationManager")
    def test_translate_command(self, mock_translation_manager_class):
        """Test the translate command."""
        mock_manager = MagicMock()
        mock_translation_manager_class.return_value = mock_manager

        call_command("translate", stdout=self.out)

        mock_manager.translate_all_po_files.assert_called_once_with(["ar"])
        self.assertIn("Successfully translated PO files for: ar", self.out.getvalue())

    @patch("apps.internationalization.management.commands.translate.TranslationManager")
    def test_translate_command_error(self, mock_translation_manager_class):
        """Test the translate command when an error occurs."""
        mock_manager = MagicMock()
        mock_manager.translate_all_po_files.side_effect = TranslationError(
            "Translation error"
        )
        mock_translation_manager_class.return_value = mock_manager

        with self.assertRaises(CommandError) as context:
            call_command("translate", stdout=self.out)

        self.assertEqual(
            str(context.exception), "Translation failed: Translation error"
        )
        mock_manager.translate_all_po_files.assert_called_once_with(["ar"])
