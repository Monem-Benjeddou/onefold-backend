"""
Comprehensive tests for User model username generation functionality.
Tests the three cases of username generation based on available data.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class UsernameGenerationTest(TestCase):
    """Test the username generation logic in User model."""

    def setUp(self):
        """Set up test data."""

        User.objects.all().delete()

    def test_case_1_fullname_based_username(self):
        """Test Case 1: Username generation from fullname when available."""

        user1 = User.objects.create_user(
            email="john.doe@example.com", password="testpass123", fullname="John Doe"
        )
        self.assertEqual(user1.username, "john_doe")

        user2 = User.objects.create_user(
            email="jane.smith@example.com",
            password="testpass123",
            fullname="Jane O'Connor-Smith",
        )
        self.assertEqual(user2.username, "jane_oconnorsmith")

        user3 = User.objects.create_user(
            email="bob.jones@example.com",
            password="testpass123",
            fullname="Bob Jones Jr 3rd",
        )
        self.assertEqual(user3.username, "bob_jones_jr_3rd")

        user4 = User.objects.create_user(
            email="alice.brown@example.com",
            password="testpass123",
            fullname="  Alice   Marie   Brown  ",
        )
        self.assertEqual(user4.username, "alice_marie_brown")

    def test_case_1_fullname_uniqueness(self):
        """Test that duplicate fullnames get unique usernames."""

        user1 = User.objects.create_user(
            email="john1@example.com", password="testpass123", fullname="John Smith"
        )
        self.assertEqual(user1.username, "john_smith")

        user2 = User.objects.create_user(
            email="john2@example.com", password="testpass123", fullname="John Smith"
        )
        self.assertEqual(user2.username, "john_smith_1")

        user3 = User.objects.create_user(
            email="john3@example.com", password="testpass123", fullname="John Smith"
        )
        self.assertEqual(user3.username, "john_smith_2")

    def test_case_2_email_prefix_based_username(self):
        """Test Case 2: Username generation from email prefix when no fullname."""

        user1 = User.objects.create_user(
            email="testuser@example.com", password="testpass123"
        )
        self.assertEqual(user1.username, "testuser")

        user2 = User.objects.create_user(
            email="john.doe.123@example.com", password="testpass123"
        )
        self.assertEqual(user2.username, "john.doe.123")

        user3 = User.objects.create_user(
            email="user+tag@example.com", password="testpass123"
        )
        self.assertEqual(user3.username, "user_tag")

        user4 = User.objects.create_user(
            email="test-user-name@example.com", password="testpass123"
        )
        self.assertEqual(user4.username, "test_user_name")

    def test_case_2_email_prefix_uniqueness(self):
        """Test that duplicate email prefixes get unique usernames."""

        user1 = User.objects.create_user(
            email="testuser@domain1.com", password="testpass123"
        )
        self.assertEqual(user1.username, "testuser")

        user2 = User.objects.create_user(
            email="testuser@domain2.com", password="testpass123"
        )
        self.assertEqual(user2.username, "testuser_1")

    def test_case_3_full_email_based_username(self):
        """Test Case 3: Username generation from full email when no @ symbol."""

        user1 = User.objects.create_user(
            email="user.domain.com", password="testpass123"
        )
        self.assertEqual(user1.username, "user_domain_com")

        user2 = User.objects.create_user(
            email="test.user@sub.domain.com", password="testpass123"
        )

        self.assertEqual(user2.username, "test.user")

    def test_case_3_full_email_uniqueness(self):
        """Test that duplicate full emails get unique usernames."""

        user1 = User.objects.create_user(
            email="user.example.com", password="testpass123"
        )
        self.assertEqual(user1.username, "user_example_com")

        user2 = User.objects.create_user(
            email="user.example.org", password="testpass123"
        )
        self.assertEqual(user2.username, "user_example_org")

    def test_edge_cases(self):
        """Test edge cases and fallback scenarios."""

        user1 = User.objects.create_user(
            email="test@example.com", password="testpass123", fullname=""
        )
        self.assertEqual(user1.username, "test")

        user2 = User.objects.create_user(
            email="test2@example.com", password="testpass123", fullname="   "
        )
        self.assertEqual(user2.username, "test2")

        user3 = User.objects.create_user(
            email="test3@example.com", password="testpass123", fullname="@#$"
        )
        self.assertEqual(user3.username, "test3")

    def test_username_length_limits(self):
        """Test username length handling."""

        long_name = "A" * 200
        user1 = User.objects.create_user(
            email="longname@example.com", password="testpass123", fullname=long_name
        )

        self.assertLessEqual(len(user1.username), 150)
        self.assertTrue(user1.username.startswith("a" * 10))

    def test_manual_username_not_overridden(self):
        """Test that manually set usernames are not overridden."""

        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            fullname="John Doe",
            username="custom_username",
        )
        self.assertEqual(user.username, "custom_username")

    def test_username_update_behavior(self):
        """Test that username is only generated on creation, not updates."""

        user = User.objects.create_user(
            email="test@example.com", password="testpass123", fullname="John Doe"
        )
        original_username = user.username
        self.assertEqual(original_username, "john_doe")

        user.fullname = "Jane Smith"
        user.save()

        self.assertEqual(user.username, original_username)

    def test_no_email_fallback(self):
        """Test fallback when no email is provided."""

        user = User(password="testpass123", fullname="John Doe")
        user.save()

        self.assertEqual(user.username, "john_doe")

        user2 = User(password="testpass123")
        user2.save()

        self.assertTrue(user2.username.startswith("user_"))
        self.assertEqual(len(user2.username), 11)
