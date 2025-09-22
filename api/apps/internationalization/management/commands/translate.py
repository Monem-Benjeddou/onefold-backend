"""Management command to translate PO files."""

import logging
import os
import sys
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.internationalization.services import (
    TranslationManager,
    TranslationError,
    get_languages,
)
from apps.internationalization.translation.utils import get_language_from_path
from typing import List, Any

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to translate PO files.

    This command uses the TranslationManager to translate all untranslated strings
    in the project's PO files. It supports multiple languages and provides options
    for controlling the translation process.

    Example:
        python manage.py translate --languages ar fr es
        python manage.py translate --clear-cache
        python manage.py translate --force
    """

    help = "Translate PO files or individual strings using the translation service"

    def add_arguments(self, parser):

        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument(
            "--all",
            action="store_true",
            help="Translate all untranslated strings in all PO files for all languages",
        )
        mode_group.add_argument("--file", help="Translate a specific PO file")
        mode_group.add_argument("--string", help="Translate a single string")
        mode_group.add_argument(
            "--list-languages",
            action="store_true",
            help="List available languages and exit",
        )

        parser.add_argument(
            "--languages",
            nargs="+",
            help="Language codes to translate to (default: all non-English languages in settings.LANGUAGES)",
        )
        parser.add_argument(
            "--source-language", default="en", help="Source language code (default: en)"
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of strings to translate in each batch (default: 1000)",
        )
        parser.add_argument(
            "--max-workers",
            type=int,
            default=5,
            help="Maximum number of worker threads for parallel processing (default: 5)",
        )
        parser.add_argument(
            "--max-entries",
            type=int,
            help="Maximum number of entries to translate per file (useful for testing or limiting translation costs)",
        )

        parser.add_argument(
            "--force",
            action="store_true",
            help="Force retranslation of already translated strings",
        )

        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed output"
        )

    def handle(self, *args, **options):

        if options["list_languages"]:
            self.list_languages()
            return

        translation_manager = TranslationManager(
            max_workers=options["max_workers"],
        )

        languages = options["languages"]
        if not languages:
            languages = [
                lang[0]
                for lang in settings.LANGUAGES
                if lang[0] != options["source_language"]
            ]

        if options["all"]:
            self.translate_all_languages(
                translation_manager=translation_manager,
                languages=languages,
                source_language=options["source_language"],
                batch_size=options["batch_size"],
                force=options["force"],
                max_entries=options["max_entries"],
                verbose=options["verbose"],
            )
        elif options["file"]:
            self.translate_file(
                translation_manager=translation_manager,
                file_path=options["file"],
                languages=languages,
                source_language=options["source_language"],
                batch_size=options["batch_size"],
                force=options["force"],
                verbose=options["verbose"],
            )
        elif options["string"]:
            self.translate_string(
                translation_manager=translation_manager,
                text=options["string"],
                languages=languages,
                source_language=options["source_language"],
                verbose=options["verbose"],
            )

    def list_languages(self):
        """List all available languages from settings."""
        languages = get_languages()
        self.stdout.write(self.style.SUCCESS("Available languages:"))
        for code, name in languages:
            self.stdout.write(f"  {code}: {name}")

    def translate_all_languages(
        self,
        translation_manager,
        languages,
        source_language,
        batch_size,
        force,
        max_entries,
        verbose,
    ):
        """Translate all PO files for all specified languages."""
        self.stdout.write(
            self.style.SUCCESS(
                f"Translating all PO files for languages: {', '.join(languages)}"
            )
        )
        self.stdout.write(
            f"Batch size: {batch_size}, Force: {force}, Max entries: {max_entries or 'unlimited'}"
        )

        start_time = time.time()

        try:
            result = translation_manager.translate_all_po_files(
                languages=languages,
                batch_size=batch_size,
                force=force,
                max_entries_per_file=max_entries,
            )

            elapsed_time = time.time() - start_time

            self.stdout.write(
                self.style.SUCCESS("\nTranslation completed successfully!")
            )
            self.stdout.write(f"Total time: {elapsed_time:.2f} seconds")
            self.stdout.write(f"Languages processed: {len(result['languages'])}")
            self.stdout.write(f"Files processed: {result['files_processed']}")
            self.stdout.write(f"Files with errors: {result['files_with_errors']}")
            self.stdout.write(f"Total entries: {result['total_entries']}")
            self.stdout.write(f"Newly translated: {result['newly_translated']}")

            if verbose:
                self.stdout.write("\nDetailed statistics by language:")
                for lang, stats in result["language_stats"].items():
                    self.stdout.write(f"\n{lang}:")
                    self.stdout.write(f"  Files found: {stats.get('files_found', 0)}")
                    self.stdout.write(
                        f"  Files processed: {stats.get('files_processed', 0)}"
                    )
                    self.stdout.write(
                        f"  Total entries: {stats.get('total_entries', 0)}"
                    )
                    self.stdout.write(
                        f"  Newly translated: {stats.get('newly_translated', 0)}"
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during translation: {e}"))
            raise CommandError(f"Translation failed: {e}")

    def translate_file(
        self,
        translation_manager,
        file_path,
        languages,
        source_language,
        batch_size,
        force,
        verbose,
    ):
        """Translate a specific PO file."""
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(self.style.SUCCESS(f"Translating file: {file_path}"))

        file_language = get_language_from_path(file_path)
        if file_language:
            languages = [file_language]
        elif not languages or len(languages) != 1:
            raise CommandError(
                "Cannot determine target language. Please specify a single language using --languages."
            )

        target_language = languages[0]
        self.stdout.write(f"Target language: {target_language}")
        self.stdout.write(f"Batch size: {batch_size}, Force: {force}")

        start_time = time.time()

        try:
            result = translation_manager.translate_po_file(
                po_file_path=file_path,
                dest_language=target_language,
                source_language=source_language,
                batch_size=batch_size,
                force=force,
            )

            elapsed_time = time.time() - start_time

            self.stdout.write(
                self.style.SUCCESS("\nTranslation completed successfully!")
            )
            self.stdout.write(f"Total time: {elapsed_time:.2f} seconds")
            self.stdout.write(f"Total entries: {result['total_entries']}")
            self.stdout.write(
                f"Already translated: {result.get('already_translated', 0)}"
            )
            self.stdout.write(f"Newly translated: {result['newly_translated']}")
            self.stdout.write(f"Errors: {result.get('errors', 0)}")

            if verbose and result.get("translations_per_second"):
                self.stdout.write(
                    f"Translations per second: {result['translations_per_second']:.2f}"
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during translation: {e}"))
            raise CommandError(f"Translation failed: {e}")

    def translate_string(
        self, translation_manager, text, languages, source_language, verbose
    ):
        """Translate a single string to all specified languages."""
        self.stdout.write(self.style.SUCCESS(f"Translating string: '{text}'"))
        self.stdout.write(f"Source language: {source_language}")
        self.stdout.write(f"Target languages: {', '.join(languages)}")

        success = True
        for language in languages:
            try:
                translated = translation_manager.translate_text(
                    text=text, dest_language=language, source_language=source_language
                )

                self.stdout.write(f"\n{language}: {translated}")

            except Exception as e:
                success = False
                self.stdout.write(
                    self.style.ERROR(f"Error translating to {language}: {e}")
                )

        if success:
            self.stdout.write(
                self.style.SUCCESS("\nTranslation completed successfully!")
            )
