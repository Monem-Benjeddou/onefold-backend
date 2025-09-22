"""Utility functions for internationalization."""

import os
import polib
import logging
from typing import Union, List, Optional
import ast
from django.conf import settings

logger = logging.getLogger(__name__)


def get_po_translated_string(
    string: str, language: str, test_mode: bool = False
) -> Optional[str]:
    """
    Returns the translated string (msgstr) for the given string (msgid) from the .po file.

    This function handles multi-line msgid and msgstr entries correctly by normalizing
    line breaks before comparison. It uses the Django locale directory structure to
    locate the appropriate .po file.

    Args:
        string: The msgid to look for in the .po file.
        language: The language code to fetch the translation for.
        test_mode: If True, returns None when no translation is found.

    Returns:
        The translated msgstr if found, the original string if not found (unless test_mode is True),
        or None if test_mode is True and no translation is found.

    Example:
        >>> get_po_translated_string("Hello", "ar")
        'مرحبا'
        >>> get_po_translated_string("NonExistent", "ar", test_mode=True)
        None
    """
    if not string or not language:
        return string if not test_mode else None

    try:
        po_file_path = os.path.join(
            settings.LOCALE_PATHS[0], language, "LC_MESSAGES", "django.po"
        )

        if not os.path.exists(po_file_path):
            logger.error(f"PO file not found: {po_file_path}")
            return None if test_mode else string

        po = polib.pofile(po_file_path)
        normalized_string = "".join(string.splitlines())

        for entry in po:
            if not entry.msgstr:
                continue

            msgid = "".join(entry.msgid.splitlines())
            if msgid == normalized_string:
                return "".join(entry.msgstr.splitlines())

        return None if test_mode else string

    except Exception as e:
        logger.error(
            f"Error retrieving translation for '{string}' in language '{language}': {e}"
        )
        return None if test_mode else string


def extract_translatable_strings(file_path: str) -> List[str]:
    """
    Extract all strings wrapped with _() from a Python file.

    This function parses the Python file's AST to find all calls to the gettext
    function (usually aliased as _) and extracts their string arguments. It handles
    both simple string literals and formatted strings.

    Args:
        file_path: The path to the Python file to analyze.

    Returns:
        A list of strings that are marked for translation.

    Example:
        >>> extract_translatable_strings("views.py")
        ['Hello', 'Welcome {name}', 'Goodbye']
    """
    translatable_strings = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()

        tree = ast.parse(file_content)

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_"
                and node.args
            ):
                arg = node.args[0]
                if isinstance(arg, ast.Str):
                    translatable_strings.append(arg.s)
                elif isinstance(arg, ast.JoinedStr):
                    parts = []
                    for value in arg.values:
                        if isinstance(value, ast.Str):
                            parts.append(value.s)
                        elif isinstance(value, ast.FormattedValue):
                            parts.append("{}")
                    translatable_strings.append("".join(parts))

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except SyntaxError as e:
        logger.error(f"Syntax error in file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while extracting strings from {file_path}: {e}")

    return translatable_strings


def is_po_file_up_to_date(po_file_path: str) -> bool:
    """
    Check if a PO file is up to date with its source files.

    This function checks the modification times of the PO file and all Python
    source files in the project to determine if the translations need updating.

    Args:
        po_file_path: Path to the PO file to check.

    Returns:
        True if the PO file is up to date, False otherwise.
    """
    if not os.path.exists(po_file_path):
        return False

    po_mtime = os.path.getmtime(po_file_path)

    for root, _, files in os.walk(settings.BASE_DIR):
        if "env" in root or "venv" in root or ".git" in root:
            continue

        for file in files:
            if file.endswith(".py"):
                py_file = os.path.join(root, file)
                if os.path.getmtime(py_file) > po_mtime:
                    return False

    return True
