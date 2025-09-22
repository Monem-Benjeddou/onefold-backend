"""
Cache manager for translations to avoid redundant API calls.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cache_manager")


class CacheManager:
    """
    Class for managing translation caches to avoid redundant API calls.
    """

    def __init__(
        self, cache_dir: str = None, target_lang: str = "ar", enabled: bool = True
    ):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory for cache files
            target_lang: Target language code (default: "ar")
            enabled: Whether caching is enabled (default: True)
        """
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path("locale/translation_cache")
        )
        os.makedirs(self.cache_dir, exist_ok=True)

        self.target_lang = target_lang
        self.enabled = enabled
        self.cache_file = self.cache_dir / f"{target_lang}_cache.json"
        self.cache: Dict[str, str] = {}
        self.modified = False

        self._load_cache()

    def _load_cache(self) -> None:
        """Load the cache from file if it exists."""
        if not self.enabled:
            return

        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                logger.info(
                    f"Loaded {len(self.cache)} entries from cache file {self.cache_file}"
                )
            else:
                logger.info(
                    f"Cache file {self.cache_file} not found, starting with empty cache"
                )
                self.cache = {}
        except Exception as e:
            logger.error(f"Error loading cache file: {e}")
            self.cache = {}

    def _save_cache(self) -> None:
        """Save the cache to file if it has been modified."""
        if not self.enabled or not self.modified:
            return

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.info(
                f"Saved {len(self.cache)} entries to cache file {self.cache_file}"
            )
            self.modified = False
        except Exception as e:
            logger.error(f"Error saving cache file: {e}")

    def get(self, source_text: str) -> Optional[str]:
        """
        Get a cached translation if it exists.

        Args:
            source_text: The source text to look up

        Returns:
            The cached translation if it exists, otherwise None
        """
        if not self.enabled:
            return None

        key = self._normalize_key(source_text)
        return self.cache.get(key)

    def set(self, source_text: str, translated_text: str) -> None:
        """
        Add a translation to the cache.

        Args:
            source_text: The source text
            translated_text: The translated text
        """
        if not self.enabled:
            return

        key = self._normalize_key(source_text)
        self.cache[key] = translated_text
        self.modified = True

        if len(self.cache) % 10 == 0:
            self._save_cache()

    def _normalize_key(self, text: str) -> str:
        """
        Normalize text to use as a cache key.
        Removes extra whitespace and other variations that don't affect meaning.

        Args:
            text: The text to normalize

        Returns:
            Normalized text for use as a cache key
        """
        return " ".join(text.split())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "target_language": self.target_lang,
            "cache_entries": len(self.cache),
            "cache_file": str(self.cache_file),
            "cache_enabled": self.enabled,
        }

    def clear(self) -> None:
        """Clear the cache."""
        self.cache = {}
        self.modified = True
        self._save_cache()
        logger.info("Cache cleared")

    def close(self) -> None:
        """Save the cache and close resources."""
        self._save_cache()

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Save cache when exiting context."""
        self.close()
