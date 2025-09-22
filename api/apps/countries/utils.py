from django.utils.translation import get_language, activate, gettext as _
from django.conf import settings
from typing import Dict, Optional


def get_country_name_translations(country_name: str) -> Dict[str, str]:
    """
    Get translations of a country name in all available languages.

    Args:
        country_name (str): The English name of the country

    Returns:
        Dict[str, str]: Dictionary mapping language codes to translated country names
    """
    translations = {}
    current_language = get_language()

    try:
        translations["en"] = country_name

        for lang_code, lang_name in settings.LANGUAGES:
            if lang_code != "en":
                activate(lang_code)
                translated_name = _(country_name)
                translations[lang_code] = translated_name
    finally:
        activate(current_language)

    return translations


def get_country_translation(country_name: str, language: Optional[str] = None) -> str:
    """
    Get the translation of a country name in a specific language.

    Args:
        country_name (str): The English name of the country
        language (str, optional): The language code. If None, uses the current language.

    Returns:
        str: The translated country name
    """
    if language is None:
        language = get_language()

    if language == "en":
        return country_name

    current_language = get_language()
    try:
        activate(language)
        translated_name = _(country_name)
        return translated_name
    finally:
        activate(current_language)
