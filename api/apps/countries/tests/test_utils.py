from django.test import TestCase, override_settings
from django.utils.translation import activate, get_language

from apps.countries.utils import get_country_name_translations, get_country_translation


class CountryTranslationUtilsTestCase(TestCase):
    """Test case for country translation utility functions."""

    def setUp(self):
        """Set up test case."""

        self.original_language = get_language()

    def tearDown(self):
        """Clean up after test case."""

        activate(self.original_language)

    def test_get_country_translation(self):
        """Test get_country_translation function."""

        activate("en")
        self.assertEqual(
            get_country_translation("United States", "en"), "United States"
        )

        arabic_translation = get_country_translation("United States", "ar")
        self.assertIsInstance(arabic_translation, str)

    def test_get_country_name_translations(self):
        """Test get_country_name_translations function."""
        translations = get_country_name_translations("Germany")

        self.assertIn("en", translations)
        self.assertEqual(translations["en"], "Germany")

        if "ar" in dict(self.client.defaults.get("LANGUAGES", [])):
            self.assertIn("ar", translations)

    @override_settings(LANGUAGE_CODE="ar")
    def test_translation_with_language_override(self):
        """Test translation with language override."""

        activate("ar")

        translation = get_country_translation("France")

        self.assertIsInstance(translation, str)

        translations = get_country_name_translations("France")

        self.assertIn("en", translations)
        self.assertEqual(translations["en"], "France")

        if "ar" in translations:
            pass
