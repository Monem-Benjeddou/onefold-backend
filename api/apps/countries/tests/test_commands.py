from io import StringIO
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command
from django.db.models import Q

from apps.accounts.user.models import User
from apps.countries.models import Country


class UpdateUserCountriesFieldsCommandTest(TestCase):
    def setUp(self):
        self.saudi_arabia = Country.objects.create(
            name="Saudi Arabia", iso2="SA", iso3="SAU", phone_code="966"
        )

        self.usa = Country.objects.create(
            name="United States", iso2="US", iso3="USA", phone_code="1"
        )

        self.france = Country.objects.create(
            name="France", iso2="FR", iso3="FRA", phone_code="33"
        )

        self.user1 = User.objects.create(
            username="user1",
            email="user1@example.com",
            phone_number="+966502345679",
            is_email_verified=True,
        )

        self.user2 = User.objects.create(
            username="user2",
            email="user2@example.com",
            phone_number="1-555-123-4567",
            is_email_verified=True,
        )

        self.user3 = User.objects.create(
            username="user3",
            email="user3@example.com",
            phone_number="+33 6 12 34 56 78",
            is_email_verified=True,
        )

        self.user4 = User.objects.create(
            username="user4",
            email="user4@example.com",
            phone_number="invalid",
            is_email_verified=True,
        )

        self.user5 = User.objects.create(
            username="user5", email="user5@example.com", is_email_verified=True
        )

        self.user6 = User.objects.create(
            username="user6",
            email="user6@example.com",
            phone_number="+966502345678",
            country=self.saudi_arabia,
            is_email_verified=True,
        )

    def test_command_output(self):
        out = StringIO()
        call_command("update_user_countries_fields", stdout=out)
        output = out.getvalue()

        self.assertIn("Completed updating user countries", output)

        self.assertIn("Success: 3", output)

        self.assertIn("Failures: 1", output)

        self.assertIn("Found 4 users with phone numbers but no country", output)

        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.user3.refresh_from_db()
        self.user4.refresh_from_db()

        self.assertEqual(self.user1.country, self.saudi_arabia)
        self.assertEqual(self.user2.country, self.usa)
        self.assertEqual(self.user3.country, self.france)
        self.assertIsNone(self.user4.country)

    def test_dry_run_mode(self):
        out = StringIO()
        call_command("update_user_countries_fields", "--dry-run", stdout=out)
        output = out.getvalue()

        self.assertIn("Running in dry-run mode", output)

        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.user3.refresh_from_db()

        self.assertIsNone(self.user1.country)
        self.assertIsNone(self.user2.country)
        self.assertIsNone(self.user3.country)

    def test_no_users_to_update(self):
        User.objects.filter(country__isnull=True).update(country=self.saudi_arabia)

        out = StringIO()
        call_command("update_user_countries_fields", stdout=out)
        output = out.getvalue()

        self.assertIn("Found 0 users with phone numbers but no country", output)
        self.assertIn("Success: 0", output)
        self.assertIn("Failures: 0", output)

    @patch(
        "apps.countries.management.commands.update_user_countries_fields.Command._guess_country_from_phone"
    )
    def test_error_handling(self, mock_guess_country):
        mock_guess_country.side_effect = Exception("Test exception")

        out = StringIO()
        call_command("update_user_countries_fields", stdout=out)
        output = out.getvalue()

        self.assertIn("Error updating user", output)
        self.assertIn("Failures: 4", output)

        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.user3.refresh_from_db()
        self.user4.refresh_from_db()

        self.assertIsNone(self.user1.country)
        self.assertIsNone(self.user2.country)
        self.assertIsNone(self.user3.country)
        self.assertIsNone(self.user4.country)

    def test_different_phone_formats(self):
        user_with_plus = User.objects.create(
            username="user_plus",
            email="user_plus@example.com",
            phone_number="+966123456789",
            is_email_verified=True,
        )

        user_without_plus = User.objects.create(
            username="user_no_plus",
            email="user_no_plus@example.com",
            phone_number="966987654321",
            is_email_verified=True,
        )

        user_with_spaces = User.objects.create(
            username="user_spaces",
            email="user_spaces@example.com",
            phone_number="+966 12 345 67 89",
            is_email_verified=True,
        )

        user_with_dashes = User.objects.create(
            username="user_dashes",
            email="user_dashes@example.com",
            phone_number="+966-12-345-67-89",
            is_email_verified=True,
        )

        out = StringIO()
        call_command("update_user_countries_fields", stdout=out)
        output = out.getvalue()

        user_with_plus.refresh_from_db()
        user_without_plus.refresh_from_db()
        user_with_spaces.refresh_from_db()
        user_with_dashes.refresh_from_db()

        self.assertEqual(user_with_plus.country, self.saudi_arabia)
        self.assertEqual(user_without_plus.country, self.saudi_arabia)
        self.assertEqual(user_with_spaces.country, self.saudi_arabia)
        self.assertEqual(user_with_dashes.country, self.saudi_arabia)
