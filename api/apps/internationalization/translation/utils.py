"""
Utility functions for handling .po files and translations.
"""

import os
import re
import logging
import polib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("translation_utils")


def parse_po_file(file_path: str) -> Tuple[polib.POFile, List[polib.POEntry]]:
    """
    Parse a .po file and extract entries that need translation.

    Args:
        file_path: Path to the .po file

    Returns:
        Tuple of POFile object and list of entries needing translation

    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: If there's an error parsing the file
    """
    try:
        po_file = polib.pofile(file_path)
        untranslated_entries = [
            entry
            for entry in po_file
            if not entry.msgstr or entry.msgstr == entry.msgid
        ]
        logger.info(
            f"Parsed {file_path}: {len(untranslated_entries)} untranslated entries out of {len(po_file)}"
        )
        return po_file, untranslated_entries
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error parsing .po file: {e}")
        raise


def write_po_file(po_file: polib.POFile, file_path: str) -> None:
    """
    Write a .po file with updated translations.

    Args:
        po_file: POFile object with translations
        file_path: Path to write the file

    Raises:
        Exception: If there's an error writing the file
    """
    try:
        po_file.save(file_path)
        logger.info(f"Saved updated translations to {file_path}")
    except Exception as e:
        logger.error(f"Error writing .po file: {e}")
        raise


def backup_po_file(file_path: str) -> str:
    """
    Create a backup of a .po file before modifying it.

    Args:
        file_path: Path to the .po file

    Returns:
        Path to the backup file

    Raises:
        Exception: If there's an error creating the backup
    """
    try:
        path = Path(file_path)
        backup_path = path.parent / f"{path.stem}.bak{path.suffix}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Created backup of {file_path} at {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise


def find_po_files(base_dir: str, language: str = None) -> List[str]:
    """
    Find all .po files in a directory tree, optionally filtering by language.

    Args:
        base_dir: Base directory to search in
        language: Optional language code to filter by

    Returns:
        List of paths to .po files
    """
    po_files = []
    base_path = Path(base_dir)

    if language:

        if base_path.name == "locale" or str(base_path).endswith("/locale"):
            locale_path = base_path / language / "LC_MESSAGES"
        else:
            locale_path = base_path / "locale" / language / "LC_MESSAGES"

        if locale_path.exists():
            for path in locale_path.glob("**/*.po"):

                if not path.name.endswith(".bak.po"):
                    po_files.append(str(path))
    else:

        if base_path.name == "locale" or str(base_path).endswith("/locale"):
            for path in base_path.glob("**/LC_MESSAGES/**/*.po"):

                if not path.name.endswith(".bak.po"):
                    po_files.append(str(path))
        else:
            for path in base_path.glob("**/locale/**/LC_MESSAGES/**/*.po"):

                if not path.name.endswith(".bak.po"):
                    po_files.append(str(path))

    logger.info(
        f"Found {len(po_files)} .po files in {base_dir} for language {language}"
    )
    return po_files


def get_language_from_path(file_path: str) -> Optional[str]:
    """
    Extract language code from a .po file path.

    Args:
        file_path: Path to the .po file

    Returns:
        Language code, or None if it couldn't be determined
    """
    match = re.search(r"locale/([^/]+)/LC_MESSAGES", file_path)
    if match:
        return match.group(1)
    return None
