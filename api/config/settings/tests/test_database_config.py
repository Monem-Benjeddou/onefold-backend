"""
Tests for database configuration with Neon.com serverless database support.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from ..config_loader import parse_database_url, get_database_config


class DatabaseConfigurationTest(TestCase):
    """Test database configuration functionality."""

    def test_parse_database_url_valid_neon_url(self):
        """Test parsing a valid Neon.com database URL."""
        neon_url = "postgresql://kolctdb_owner:npg_lk3gSFq9KGbN@ep-tight-sea-a2shj9rq-pooler.eu-central-1.aws.neon.tech/kolctdb?sslmode=require&channel_binding=require"

        config = parse_database_url(neon_url)

        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(config["NAME"], "kolctdb")
        self.assertEqual(config["USER"], "kolctdb_owner")
        self.assertEqual(config["PASSWORD"], "npg_lk3gSFq9KGbN")
        self.assertEqual(
            config["HOST"], "ep-tight-sea-a2shj9rq-pooler.eu-central-1.aws.neon.tech"
        )
        self.assertEqual(config["PORT"], 5432)
        self.assertIn("OPTIONS", config)
        self.assertEqual(config["OPTIONS"]["sslmode"], "require")
        self.assertEqual(config["OPTIONS"]["channel_binding"], "require")

    def test_parse_database_url_simple_postgresql(self):
        """Test parsing a simple PostgreSQL URL."""
        simple_url = "postgresql://user:pass@localhost:5432/mydb"

        config = parse_database_url(simple_url)

        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(config["NAME"], "mydb")
        self.assertEqual(config["USER"], "user")
        self.assertEqual(config["PASSWORD"], "pass")
        self.assertEqual(config["HOST"], "localhost")
        self.assertEqual(config["PORT"], 5432)

    def test_parse_database_url_empty_string(self):
        """Test parsing an empty database URL."""
        config = parse_database_url("")
        self.assertEqual(config, {})

    def test_parse_database_url_none(self):
        """Test parsing None database URL."""
        config = parse_database_url(None)
        self.assertEqual(config, {})

    def test_parse_database_url_invalid_url(self):
        """Test parsing an invalid database URL."""
        invalid_url = "not-a-valid-url"
        config = parse_database_url(invalid_url)

        self.assertEqual(config, {})

    @patch("config.settings.config_loader.get_secure_value")
    @patch("config.settings.config_loader.get_environment")
    @patch("config.settings.config_loader.get_config_value")
    def test_get_database_config_with_neon_url(
        self, mock_get_config_value, mock_get_environment, mock_get_secure_value
    ):
        """Test get_database_config when NEON_DATABASE_URL is provided."""

        mock_get_environment.return_value = "production"
        mock_get_config_value.return_value = {}

        def mock_secure_value_side_effect(key, default=None):
            if key == "NEON_DATABASE_URL":
                return "postgresql://user:pass@host:5432/db?sslmode=require"
            return default

        mock_get_secure_value.side_effect = mock_secure_value_side_effect

        config = get_database_config()

        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(config["NAME"], "db")
        self.assertEqual(config["USER"], "user")
        self.assertEqual(config["PASSWORD"], "pass")
        self.assertEqual(config["HOST"], "host")
        self.assertEqual(config["PORT"], 5432)
        self.assertIn("OPTIONS", config)
        self.assertEqual(config["OPTIONS"]["sslmode"], "require")
        self.assertEqual(config["OPTIONS"]["connect_timeout"], 10)
        self.assertTrue(config["ATOMIC_REQUESTS"])
        self.assertEqual(config["CONN_MAX_AGE"], 60)

    @patch("config.settings.config_loader.get_secure_value")
    @patch("config.settings.config_loader.get_environment")
    @patch("config.settings.config_loader.get_config_value")
    @patch("config.settings.config_loader.get_env_int")
    def test_get_database_config_fallback_to_env_vars(
        self,
        mock_get_env_int,
        mock_get_config_value,
        mock_get_environment,
        mock_get_secure_value,
    ):
        """Test get_database_config fallback to traditional environment variables."""

        mock_get_environment.return_value = "development"
        mock_get_config_value.return_value = {}
        mock_get_env_int.return_value = 5432

        def mock_secure_value_side_effect(key, default=None):
            if key == "NEON_DATABASE_URL":
                return None
            elif key == "DATABASE_NAME":
                return "test_db"
            elif key == "DATABASE_USER":
                return "test_user"
            elif key == "DATABASE_PASSWORD":
                return "test_pass"
            elif key == "DATABASE_HOST":
                return "localhost"
            return default

        mock_get_secure_value.side_effect = mock_secure_value_side_effect

        config = get_database_config()

        self.assertEqual(config["NAME"], "test_db")
        self.assertEqual(config["USER"], "test_user")
        self.assertEqual(config["PASSWORD"], "test_pass")
        self.assertEqual(config["HOST"], "localhost")
        self.assertEqual(config["PORT"], 5432)
        self.assertTrue(config["ATOMIC_REQUESTS"])
        self.assertEqual(config["CONN_MAX_AGE"], 60)

    def test_database_url_with_special_characters(self):
        """Test parsing database URL with special characters in password."""
        url_with_special_chars = "postgresql://user:p%40ssw%24rd@host:5432/db"

        config = parse_database_url(url_with_special_chars)

        self.assertEqual(config["USER"], "user")
        self.assertEqual(config["PASSWORD"], "p@ssw$rd")
        self.assertEqual(config["HOST"], "host")
        self.assertEqual(config["NAME"], "db")

    def test_database_url_without_port(self):
        """Test parsing database URL without explicit port."""
        url_without_port = "postgresql://user:pass@host/db"

        config = parse_database_url(url_without_port)

        self.assertEqual(config["PORT"], 5432)

    def test_database_url_with_custom_port(self):
        """Test parsing database URL with custom port."""
        url_with_port = "postgresql://user:pass@host:3306/db"

        config = parse_database_url(url_with_port)

        self.assertEqual(config["PORT"], 3306)
