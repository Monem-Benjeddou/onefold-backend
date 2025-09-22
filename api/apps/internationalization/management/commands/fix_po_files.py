"""Management command to fix common PO file issues."""

import os
import re
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
import polib

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to fix common PO file issues that cause compilemessages to fail.

    This command:
    - Validates PO file syntax
    - Fixes common formatting issues
    - Removes invalid entries
    - Ensures proper headers
    """

    help = "Fix common PO file issues that cause compilemessages to fail"

    def add_arguments(self, parser):
        parser.add_argument(
            "--languages",
            nargs="+",
            help="Language codes to fix (default: all configured languages)",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed output"
        )

    def handle(self, *args, **options):
        languages = options["languages"]
        if not languages:
            languages = [lang[0] for lang in settings.LANGUAGES if lang[0] != "en"]

        verbose = options["verbose"]

        for language in languages:
            self.fix_language_po_files(language, verbose)

    def fix_language_po_files(self, language: str, verbose: bool = False):
        """Fix PO files for a specific language."""
        self.stdout.write(f"Fixing PO files for language: {language}")

        locale_dir = settings.LOCALE_PATHS[0] if settings.LOCALE_PATHS else "locale"
        po_file_path = os.path.join(locale_dir, language, "LC_MESSAGES", "django.po")

        if not os.path.exists(po_file_path):
            self.stdout.write(f"PO file not found: {po_file_path}")
            return

        try:

            po = polib.pofile(po_file_path)

            issues_fixed = 0

            issues_fixed += self.fix_headers(po, language)
            issues_fixed += self.fix_entries(po, verbose)
            issues_fixed += self.remove_invalid_entries(po, verbose)

            if issues_fixed > 0:

                po.save(po_file_path)
                self.stdout.write(
                    self.style.SUCCESS(f"Fixed {issues_fixed} issues in {po_file_path}")
                )
            else:
                self.stdout.write(f"No issues found in {po_file_path}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fixing {po_file_path}: {e}"))

    def fix_headers(self, po: polib.POFile, language: str) -> int:
        """Fix PO file headers."""
        fixes = 0

        required_headers = {
            "Content-Type": "text/plain; charset=UTF-8",
            "Content-Transfer-Encoding": "8bit",
            "Language": language,
        }

        for key, value in required_headers.items():
            if key not in po.metadata or not po.metadata[key]:
                po.metadata[key] = value
                fixes += 1

        plural_forms = {
            "ar": "nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5;",
            "fr": "nplurals=2; plural=(n > 1);",
            "es": "nplurals=2; plural=(n != 1);",
            "de": "nplurals=2; plural=(n != 1);",
            "it": "nplurals=2; plural=(n != 1);",
        }

        if language in plural_forms and "Plural-Forms" not in po.metadata:
            po.metadata["Plural-Forms"] = plural_forms[language]
            fixes += 1

        return fixes

    def fix_entries(self, po: polib.POFile, verbose: bool = False) -> int:
        """Fix common issues in PO entries."""
        fixes = 0

        for entry in po:

            if not entry.msgid:
                continue

            if entry.msgstr:
                try:
                    encoded = entry.msgstr.encode("utf-8").decode("utf-8")
                    if encoded != entry.msgstr:
                        entry.msgstr = encoded
                        fixes += 1
                        if verbose:
                            self.stdout.write(
                                f"Fixed encoding for: {entry.msgid[:50]}..."
                            )
                except UnicodeError:
                    entry.msgstr = entry.msgstr.encode("utf-8", errors="ignore").decode(
                        "utf-8"
                    )
                    fixes += 1
                    if verbose:
                        self.stdout.write(
                            f"Cleaned invalid chars for: {entry.msgid[:50]}..."
                        )

            if entry.msgstr and self.has_format_string_errors(entry):

                entry.msgstr = ""
                fixes += 1
                if verbose:
                    self.stdout.write(
                        f"Cleared format string errors for: {entry.msgid[:50]}..."
                    )

            if entry.msgstr and "fuzzy" in entry.flags:
                entry.flags.remove("fuzzy")
                fixes += 1
                if verbose:
                    self.stdout.write(f"Removed fuzzy flag for: {entry.msgid[:50]}...")

        return fixes

    def has_format_string_errors(self, entry: polib.POEntry) -> bool:
        """Check if entry has format string errors."""
        import re

        if not entry.msgstr or not entry.msgid:
            return False

        if "python-format" in entry.flags or "#, python-format" in str(entry):
            try:

                msgid_params = set(re.findall(r"%\(([^)]+)\)s", entry.msgid))
                msgstr_params = set(re.findall(r"%\(([^)]+)\)s", entry.msgstr))

                if msgid_params != msgstr_params:
                    return True

                msgid_braces = len(re.findall(r"\{[^}]*\}", entry.msgid))
                msgstr_braces = len(re.findall(r"\{[^}]*\}", entry.msgstr))

                if msgid_braces != msgstr_braces:
                    return True

                if msgid_params:
                    test_dict = {param: "test" for param in msgid_params}
                    try:
                        entry.msgstr % test_dict
                    except (ValueError, KeyError, TypeError):
                        return True

            except Exception:
                return True

        return False

    def remove_invalid_entries(self, po: polib.POFile, verbose: bool = False) -> int:
        """Remove entries that cause compilation issues."""
        fixes = 0
        entries_to_remove = []

        for entry in po:

            if not entry.msgid:
                continue

            problematic_patterns = [
                r"%\([^)]*\)[^sdcfge%]",
                r'\\[^nrt"\\]',
            ]

            for pattern in problematic_patterns:
                if re.search(pattern, entry.msgstr or ""):
                    entries_to_remove.append(entry)
                    fixes += 1
                    if verbose:
                        self.stdout.write(f"Marked for removal: {entry.msgid[:50]}...")
                    break

        for entry in entries_to_remove:
            po.remove(entry)

        return fixes
