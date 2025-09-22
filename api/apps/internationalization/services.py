"""Translation management service."""

import os
import json
import subprocess
import polib
import logging
import time
from filelock import FileLock
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from django.core.cache import cache
from django.conf import settings
from django.utils.module_loading import import_string
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache


from apps.internationalization.translation.cache_manager import CacheManager
from apps.internationalization.translation.utils import (
    parse_po_file,
    write_po_file,
    backup_po_file,
    find_po_files,
)

logger = logging.getLogger(__name__)

LOCALE_DIR = settings.LOCALE_PATHS[0] if settings.LOCALE_PATHS else "locale"
TRANSLATION_CACHE_DIR = os.path.join(LOCALE_DIR, "translation_cache")
TRANSLATION_LOCK_FILE = os.path.join(LOCALE_DIR, "translation.lock")
CACHE_TIMEOUT = 60 * 60 * 24


class TranslationError(Exception):
    """Base exception for translation errors."""

    pass


class TranslationCacheError(TranslationError):
    """Exception raised for translation cache errors."""

    pass


class TranslationFileError(TranslationError):
    """Exception raised for translation file errors."""

    pass


class TranslationManager:
    """Manages translation operations including caching and file handling."""

    def __init__(self, max_workers: int = 5, use_ollama: bool = False):
        """
        Initialize the translation manager.

        Args:
            max_workers: Maximum number of worker threads for parallel processing
            use_ollama: Whether to use Ollama for translation (default: False)
        """
        self.max_workers = max_workers
        self.use_ollama = use_ollama
        self.translator = None
        self.caches = {}

        os.makedirs(TRANSLATION_CACHE_DIR, exist_ok=True)

    def _get_cache_manager(self, language: str) -> CacheManager:
        """
        Get a cached CacheManager instance for the specified language.

        Args:
            language: Target language code

        Returns:
            CacheManager instance
        """
        if language not in self.caches:
            cache_dir = TRANSLATION_CACHE_DIR
            self.caches[language] = CacheManager(
                cache_dir=cache_dir, target_lang=language, enabled=True
            )
        return self.caches[language]

    def _get_translator(
        self, source_lang: str, target_lang: str
    ) -> "googletrans.Translator":
        """
        Get a translator instance configured for the specified languages.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            GoogleTranslator instance
        """
        if self.translator is None:
            from googletrans import Translator as GoogleTranslator

            self.translator = GoogleTranslator()
        return self.translator

    def _normalize_arabic(self, text: str) -> str:
        """
        Normalize Arabic text by removing diacritics.

        Args:
            text: Arabic text to normalize

        Returns:
            Normalized text
        """
        diacritics = ["ً", "ٌ", "ٍ", "َ", "ُ", "ِ", "ّ", "ْ"]
        for diacritic in diacritics:
            text = text.replace(diacritic, "")
        return text

    def translate_text(
        self, text: str, dest_language: str, source_language: str = "en"
    ) -> str:
        """
        Translate a single text string to the target language with caching.

        Args:
            text: The text to translate
            dest_language: The target language code
            source_language: The source language code

        Returns:
            The translated text, or the original text if translation fails
        """
        if not text or text.isspace():
            return text

        cache_manager = self._get_cache_manager(dest_language)
        cached_translation = cache_manager.get(text)
        if cached_translation:
            return cached_translation

        translator = self._get_translator(source_language, dest_language)

        try:
            if self.use_ollama:

                translated_text = translator.translate_text(text)
            else:

                translation = translator.translate(
                    text, dest=dest_language, src=source_language
                )
                translated_text = translation.text

            if dest_language == "ar":
                translated_text = self._normalize_arabic(translated_text)

            cache_manager.set(text, translated_text)

            return translated_text
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text

    def translate_texts_batch(
        self, texts: List[str], dest_language: str, source_language: str = "en"
    ) -> Dict[str, str]:
        """
        Translate multiple texts in parallel using thread pool with caching.

        Args:
            texts: List of texts to translate
            dest_language: The target language code
            source_language: The source language code

        Returns:
            Dictionary mapping original texts to their translations
        """
        if not texts:
            return {}

        cache_manager = self._get_cache_manager(dest_language)

        texts_to_translate = []
        results = {}

        for text in texts:
            if not text or text.isspace():
                results[text] = text
                continue

            cached = cache_manager.get(text)
            if cached:
                results[text] = cached
            else:
                texts_to_translate.append(text)

        if not texts_to_translate:
            return results

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_text = {
                executor.submit(
                    self.translate_text, text, dest_language, source_language
                ): text
                for text in texts_to_translate
            }

            for future in as_completed(future_to_text):
                text = future_to_text[future]
                try:
                    results[text] = future.result()
                except Exception as e:
                    logger.error(f"Error translating text '{text}': {e}")
                    results[text] = text

        cache_manager._save_cache()

        return results

    def translate_po_file(
        self,
        po_file_path: str,
        dest_language: str,
        source_language: str = "en",
        batch_size: int = 100,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Translate all untranslated entries in a .po file and update the msgstr fields.

        Args:
            po_file_path: Path to the PO file
            dest_language: The target language code
            source_language: The source language code
            batch_size: Number of entries to translate at once
            force: Whether to retranslate already translated entries

        Returns:
            Dictionary with translation statistics

        Raises:
            TranslationFileError: If there's an error with the PO file
        """
        start_time = time.time()

        try:

            po_file, untranslated_entries = parse_po_file(po_file_path)

            if not untranslated_entries and not force:
                logger.info(f"All entries in {po_file_path} are already translated")
                return {
                    "file": po_file_path,
                    "total_entries": len(po_file),
                    "translated_entries": len(po_file),
                    "newly_translated": 0,
                    "time_elapsed": time.time() - start_time,
                }

            backup_file = backup_po_file(po_file_path)

            entries_to_translate = po_file if force else untranslated_entries

            stats = {
                "file": po_file_path,
                "total_entries": len(po_file),
                "already_translated": len(po_file) - len(untranslated_entries),
                "to_translate": len(entries_to_translate),
                "newly_translated": 0,
                "errors": 0,
            }

            for i in range(0, len(entries_to_translate), batch_size):
                batch = entries_to_translate[i : i + batch_size]
                logger.info(
                    f"Processing batch {i//batch_size + 1}/{(len(entries_to_translate) + batch_size - 1)//batch_size}"
                )

                texts_to_translate = [
                    entry.msgid
                    for entry in batch
                    if entry.msgid and not entry.msgid.isspace()
                ]

                translations = self.translate_texts_batch(
                    texts=texts_to_translate,
                    dest_language=dest_language,
                    source_language=source_language,
                )

                for entry in batch:
                    source_text = entry.msgid
                    if not source_text or source_text.isspace():
                        continue

                    translated_text = translations.get(source_text)
                    if translated_text and translated_text != source_text:

                        if len(translated_text.strip()) > 0:
                            entry.msgstr = translated_text
                            stats["newly_translated"] += 1
                            logger.debug(
                                f"Translated: '{source_text}' -> '{translated_text}'"
                            )
                        else:
                            logger.warning(f"Empty translation for: '{source_text}'")
                            stats["errors"] += 1
                    else:
                        logger.warning(f"No translation for: '{source_text}'")
                        stats["errors"] += 1

                write_po_file(po_file, po_file_path)

            write_po_file(po_file, po_file_path)

            elapsed_time = time.time() - start_time
            stats["time_elapsed"] = elapsed_time
            stats["translations_per_second"] = (
                stats["newly_translated"] / elapsed_time if elapsed_time > 0 else 0
            )

            logger.info(
                f"Translation completed: {stats['newly_translated']} entries translated in {elapsed_time:.2f} seconds"
            )

            return stats

        except Exception as e:
            logger.error(f"Error translating file {po_file_path}: {e}")
            raise TranslationFileError(f"Error translating file: {str(e)}")

    def translate_all_po_files(
        self,
        languages: Optional[List[str]] = None,
        batch_size: int = 1000,
        force: bool = False,
        max_entries_per_file: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Translate all PO files for the specified languages.

        Args:
            languages: List of language codes to translate to (if None, uses settings.LANGUAGES)
            batch_size: Number of entries to translate in each batch
            force: Whether to retranslate already translated entries
            max_entries_per_file: Maximum number of untranslated entries to process per file

        Returns:
            Dictionary with translation statistics
        """
        start_time = time.time()

        if languages is None:
            languages = [lang[0] for lang in settings.LANGUAGES if lang[0] != "en"]

        stats = {
            "languages": languages,
            "files_processed": 0,
            "files_with_errors": 0,
            "total_entries": 0,
            "newly_translated": 0,
            "language_stats": {},
        }

        for language in languages:
            logger.info(f"Processing language: {language}")

            try:

                try:
                    subprocess.run(
                        ["python", "manage.py", "makemessages", "-l", language],
                        check=True,
                        capture_output=True,
                    )
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Warning: makemessages failed for {language}: {e}")

                po_files = find_po_files(LOCALE_DIR, language)

                language_stats = {
                    "files_found": len(po_files),
                    "files_processed": 0,
                    "files_with_errors": 0,
                    "total_entries": 0,
                    "newly_translated": 0,
                    "file_stats": [],
                }

                for file_path in po_files:
                    logger.info(f"Processing file: {file_path}")

                    try:
                        file_stats = self.translate_po_file(
                            po_file_path=file_path,
                            dest_language=language,
                            source_language="en",
                            batch_size=batch_size,
                            force=force,
                        )

                        language_stats["files_processed"] += 1
                        language_stats["total_entries"] += file_stats.get(
                            "total_entries", 0
                        )
                        language_stats["newly_translated"] += file_stats.get(
                            "newly_translated", 0
                        )
                        language_stats["file_stats"].append(file_stats)

                        stats["files_processed"] += 1
                        stats["total_entries"] += file_stats.get("total_entries", 0)
                        stats["newly_translated"] += file_stats.get(
                            "newly_translated", 0
                        )

                        if (
                            max_entries_per_file is not None
                            and file_stats.get("newly_translated", 0)
                            >= max_entries_per_file
                        ):
                            break

                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                        language_stats["files_with_errors"] += 1
                        stats["files_with_errors"] += 1

                try:
                    result = subprocess.run(
                        ["python", "manage.py", "compilemessages", "-l", language],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    logger.info(f"Successfully compiled messages for {language}")
                except subprocess.CalledProcessError as e:
                    logger.warning(
                        f"Warning: compilemessages failed for {language}: {e.stderr if e.stderr else str(e)}"
                    )

                stats["language_stats"][language] = language_stats

            except Exception as e:
                logger.error(f"Error processing language {language}: {e}")
                stats["language_stats"][language] = {"error": str(e)}

        stats["time_elapsed"] = time.time() - start_time

        return stats

    def clear_translation_cache(self, dest_language: Optional[str] = None) -> None:
        """
        Clear the translation cache for a specific language or all languages.

        Args:
            dest_language: The target language code, or None to clear all caches
        """
        if dest_language:

            cache_path = os.path.join(TRANSLATION_CACHE_DIR, f"{dest_language}.json")
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                    logger.info(f"Cleared translation cache for {dest_language}")
                except Exception as e:
                    logger.error(
                        f"Error clearing translation cache for {dest_language}: {e}"
                    )
                    raise TranslationCacheError(f"Error clearing cache: {str(e)}")

            if dest_language in self.caches:
                self.caches[dest_language].clear()
                del self.caches[dest_language]
        else:

            for file in os.listdir(TRANSLATION_CACHE_DIR):
                if file.endswith(".json"):
                    try:
                        os.remove(os.path.join(TRANSLATION_CACHE_DIR, file))
                    except Exception as e:
                        logger.error(f"Error removing cache file {file}: {e}")

            self.caches = {}
            logger.info("Cleared all translation caches")


def get_languages() -> List[Tuple[str, str]]:
    """
    Get the list of available languages from Django settings.

    Returns:
        List of (language_code, language_name) tuples
    """
    return getattr(settings, "LANGUAGES", [("en", "English")])
