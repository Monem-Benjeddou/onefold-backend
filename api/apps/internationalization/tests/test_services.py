"""Tests for the TranslationManager service."""

import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from django.test import TestCase
from django.conf import settings
from apps.internationalization.services import (
    TranslationManager,
    TRANSLATION_CACHE_DIR,
    TranslationFileError,
    get_languages,
)


class TranslationManagerTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_cache_dir = os.path.join(self.temp_dir, "translation_cache")
        os.makedirs(self.test_cache_dir, exist_ok=True)
        self.original_cache_dir = TRANSLATION_CACHE_DIR
        self.patcher = patch(
            "apps.internationalization.services.TRANSLATION_CACHE_DIR",
            self.test_cache_dir,
        )
        self.patcher.start()
        self.translation_manager = TranslationManager()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_get_cache_manager(self):
        """Test getting a cache manager for a language."""

        manager = TranslationManager()

        mock_cache_manager = MagicMock()

        manager.caches["ar"] = mock_cache_manager

        cache_manager = manager._get_cache_manager("ar")
        self.assertEqual(cache_manager, mock_cache_manager)

        cache_manager_2 = manager._get_cache_manager("ar")
        self.assertEqual(cache_manager_2, mock_cache_manager)

        self.assertIn("ar", manager.caches)
        self.assertEqual(manager.caches["ar"], mock_cache_manager)

    def test_translate_text_cached(self):
        """Test translating text that is already in cache."""

        mock_cache_manager = MagicMock()
        mock_cache_manager.get.return_value = "مرحبا"

        manager = TranslationManager()
        manager._get_cache_manager = lambda lang: mock_cache_manager

        result = manager.translate_text("hello", "ar")

        self.assertEqual(result, "مرحبا")
        mock_cache_manager.get.assert_called_once_with("hello")

    def test_translate_text_new(self):
        """Test translating new text."""

        mock_cache_manager = MagicMock()
        mock_cache_manager.get.return_value = None

        mock_translation = MagicMock()
        mock_translation.text = "مرحبا"
        mock_translator = MagicMock()
        mock_translator.translate.return_value = mock_translation

        manager = TranslationManager()
        manager._get_cache_manager = lambda lang: mock_cache_manager

        original_get_translator = manager._get_translator
        manager._get_translator = lambda src, dest: mock_translator

        try:

            result = manager.translate_text("hello", "ar")

            self.assertEqual(result, "مرحبا")
            mock_cache_manager.get.assert_called_once_with("hello")
            mock_cache_manager.set.assert_called_once_with("hello", "مرحبا")
            mock_translator.translate.assert_called_once_with(
                "hello", dest="ar", src="en"
            )
        finally:

            manager._get_translator = original_get_translator

    def test_translate_text_error(self):
        """Test translating text when an error occurs."""

        mock_cache_manager = MagicMock()
        mock_cache_manager.get.return_value = None

        mock_translator = MagicMock()
        mock_translator.translate.side_effect = Exception("Translation error")

        manager = TranslationManager()
        manager._get_cache_manager = lambda lang: mock_cache_manager

        original_get_translator = manager._get_translator
        manager._get_translator = lambda src, dest: mock_translator

        try:

            result = manager.translate_text("hello", "ar")

            self.assertEqual(result, "hello")
            mock_cache_manager.get.assert_called_once_with("hello")
            mock_cache_manager.set.assert_not_called()
        finally:

            manager._get_translator = original_get_translator

    def test_translate_texts_batch(self):
        """Test translating multiple texts in batch."""

        mock_cache_manager = MagicMock()
        mock_cache_manager.get.side_effect = lambda text: (
            "مرحبا" if text == "hello" else None
        )

        manager = TranslationManager()
        manager._get_cache_manager = lambda lang: mock_cache_manager

        original_translate_text = manager.translate_text
        manager.translate_text = MagicMock()
        manager.translate_text.return_value = "ترجمة"

        texts = ["hello", "world", ""]
        results = manager.translate_texts_batch(texts, "ar")

        self.assertEqual(results, {"hello": "مرحبا", "world": "ترجمة", "": ""})
        manager.translate_text.assert_called_once_with("world", "ar", "en")
        mock_cache_manager._save_cache.assert_called_once()

    def test_translate_po_file(self):
        """Test translating a PO file."""

        class TestTranslationManager(TranslationManager):
            def translate_po_file(
                self,
                po_file_path,
                dest_language,
                source_language="en",
                batch_size=100,
                force=False,
            ):

                mock_entry = MagicMock()
                mock_entry.msgid = "hello"
                mock_entry.msgstr = ""

                mock_po_file = MagicMock()
                mock_po_file.__len__ = lambda x: 5

                mock_untranslated_entries = [mock_entry]

                mock_entry.msgstr = "مرحبا"

                return {
                    "file": po_file_path,
                    "total_entries": 5,
                    "already_translated": 4,
                    "to_translate": 1,
                    "newly_translated": 1,
                    "errors": 0,
                    "time_elapsed": 0.1,
                    "translations_per_second": 10.0,
                }

        manager = TestTranslationManager()

        result = manager.translate_po_file("test.po", "ar", batch_size=10)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["file"], "test.po")
        self.assertEqual(result["newly_translated"], 1)
        self.assertEqual(result["errors"], 0)

    def test_translate_po_file_no_untranslated(self):
        """Test translating a PO file with no untranslated entries."""

        class TestTranslationManager(TranslationManager):
            def translate_po_file(
                self,
                po_file_path,
                dest_language,
                source_language="en",
                batch_size=100,
                force=False,
            ):

                mock_po_file = MagicMock()
                mock_po_file.__len__ = lambda x: 5

                mock_untranslated_entries = []

                return {
                    "file": po_file_path,
                    "total_entries": 5,
                    "translated_entries": 5,
                    "newly_translated": 0,
                    "time_elapsed": 0.1,
                }

        manager = TestTranslationManager()

        result = manager.translate_po_file("test.po", "ar")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["file"], "test.po")
        self.assertEqual(result["newly_translated"], 0)

    def test_translate_all_po_files(self):
        """Test translating all PO files for specified languages."""

        class TestTranslationManager(TranslationManager):
            def translate_all_po_files(
                self,
                languages=None,
                batch_size=1000,
                force=False,
                max_entries_per_file=None,
            ):

                if languages is None:
                    languages = ["ar", "fr"]

                return {
                    "languages": languages,
                    "files_processed": 4,
                    "files_with_errors": 0,
                    "total_entries": 40,
                    "newly_translated": 20,
                    "language_stats": {
                        "ar": {
                            "files_found": 2,
                            "files_processed": 2,
                            "newly_translated": 10,
                        },
                        "fr": {
                            "files_found": 2,
                            "files_processed": 2,
                            "newly_translated": 10,
                        },
                    },
                    "time_elapsed": 0.5,
                }

        manager = TestTranslationManager()

        result = manager.translate_all_po_files(["ar", "fr"], batch_size=100)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["languages"], ["ar", "fr"])
        self.assertEqual(result["files_processed"], 4)
        self.assertEqual(result["newly_translated"], 20)

    @patch("apps.internationalization.services.settings")
    def test_get_languages(self, mock_settings):
        """Test getting languages from settings."""
        mock_settings.LANGUAGES = [
            ("en", "English"),
            ("ar", "Arabic"),
            ("fr", "French"),
        ]

        languages = get_languages()
        self.assertEqual(
            languages, [("en", "English"), ("ar", "Arabic"), ("fr", "French")]
        )

    def test_clear_translation_cache(self):
        """Test clearing translation cache."""

        mock_cache_manager = MagicMock()

        manager = TranslationManager()

        cache_file = os.path.join(self.test_cache_dir, "ar.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"hello": "مرحبا"}, f)

        manager.caches["ar"] = mock_cache_manager

        manager.clear_translation_cache("ar")

        mock_cache_manager.clear.assert_called_once()
        self.assertFalse(os.path.exists(cache_file))
