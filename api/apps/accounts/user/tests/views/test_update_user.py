from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from apps.accounts.user.models import User


@override_settings(RATE_LIMITER_ENABLED=False)
class UpdateUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.user_to_update = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Password123",
            fullname="Test User Original",
            role="user",
        )

        self.url = reverse("update-user", kwargs={"pk": self.user_to_update.pk})

        self.client.force_authenticate(user=self.admin_user)

        self.valid_data = {
            "fullname": "Updated User Name",
            "role": "admin",
        }

    def test_update_user_authenticated_as_admin(self):
        """Test updating a user when authenticated as admin"""
        response = self.client.put(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fullname"], self.valid_data["fullname"])
        self.assertEqual(response.data["role"], self.valid_data["role"])

        self.user_to_update.refresh_from_db()
        self.assertEqual(self.user_to_update.fullname, self.valid_data["fullname"])
        self.assertEqual(self.user_to_update.role, self.valid_data["role"])

    def test_update_user_with_empty_fullname(self):
        """Test that updating with empty fullname is rejected"""
        data = self.valid_data.copy()
        data["fullname"] = ""

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user_to_update.refresh_from_db()
        self.assertNotEqual(self.user_to_update.fullname, "")

    def test_update_nonexistent_user(self):
        """Test updating a user that doesn't exist"""
        non_existent_url = reverse("update-user", kwargs={"pk": uuid.uuid4()})

        response = self.client.put(non_existent_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_user_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        response = self.client.put(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_as_regular_user(self):
        """Test that regular users cannot update users"""
        regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="Password123",
            role="user",
        )
        self.client.force_authenticate(user=regular_user)

        response = self.client.put(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_with_duplicate_email(self):
        """Test that updating with an existing email is rejected"""

        existing_user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="Password123",
            role="user",
        )

        data = self.valid_data.copy()
        data["email"] = existing_user.email

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        if "error" in response.data:
            self.assertIn("email", response.data["error"])
            self.assertIn(
                "A user with this email already exists",
                str(response.data["error"]["email"]),
            )
        else:
            self.assertIn("email", response.data)
            self.assertIn(
                "A user with this email already exists", str(response.data["email"])
            )

        self.user_to_update.refresh_from_db()
        self.assertNotEqual(self.user_to_update.email, existing_user.email)

    def test_update_user_with_duplicate_phone_number(self):
        """Test that updating with an existing phone number is rejected"""

        existing_user = User.objects.create_user(
            username="existinguser2",
            email="existing2@example.com",
            password="Password123",
            phone_number="+1234567890",
            role="user",
        )

        data = self.valid_data.copy()
        data["phone_number"] = existing_user.phone_number

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        if "error" in response.data:
            self.assertIn("phone_number", response.data["error"])
            self.assertIn(
                "A user with this phone number already exists",
                str(response.data["error"]["phone_number"]),
            )
        else:
            self.assertIn("phone_number", response.data)
            self.assertIn(
                "A user with this phone number already exists",
                str(response.data["phone_number"]),
            )

        self.user_to_update.refresh_from_db()
        self.assertNotEqual(
            self.user_to_update.phone_number, existing_user.phone_number
        )

    def test_update_user_with_same_email_allowed(self):
        """Test that updating with the same email (no change) is allowed"""
        data = self.valid_data.copy()
        data["email"] = self.user_to_update.email

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_to_update.email)

    def test_update_user_with_same_phone_number_allowed(self):
        """Test that updating with the same phone number (no change) is allowed"""

        self.user_to_update.phone_number = "+1987654321"
        self.user_to_update.save()

        data = self.valid_data.copy()
        data["phone_number"] = self.user_to_update.phone_number

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["phone_number"], self.user_to_update.phone_number
        )

    def test_update_user_with_invalid_email_format(self):
        """Test that updating with invalid email format is rejected"""
        invalid_emails = [
            "invalid-email",
            "invalid@",
            "@invalid.com",
            "invalid@invalid",
            "invalid.email.com",
        ]

        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                data = self.valid_data.copy()
                data["email"] = invalid_email

                response = self.client.put(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

                if "error" in response.data:
                    self.assertIn("email", response.data["error"])
                else:
                    self.assertIn("email", response.data)

    def test_update_user_with_invalid_phone_number_format(self):
        """Test that updating with invalid phone number format is rejected"""
        invalid_phones = [
            "abc123",
            "123",
            "!@#$%",
            "123abc456",
        ]

        for invalid_phone in invalid_phones:
            with self.subTest(phone=invalid_phone):
                data = self.valid_data.copy()
                data["phone_number"] = invalid_phone

                response = self.client.put(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

                if "error" in response.data:
                    self.assertIn("phone_number", response.data["error"])
                else:
                    self.assertIn("phone_number", response.data)

    def test_update_user_with_valid_phone_number_formats(self):
        """Test that updating with valid phone number formats is accepted"""
        valid_phones = [
            "+1234567890",
            "123-456-7890",
            "(123)456-7890",
            "1234567890",
            "+441234567890",
        ]

        for valid_phone in valid_phones:
            with self.subTest(phone=valid_phone):
                data = self.valid_data.copy()
                data["phone_number"] = valid_phone

                response = self.client.put(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["phone_number"], valid_phone)

                self.user_to_update.phone_number = None
                self.user_to_update.save()

    def test_update_user_with_valid_email_formats(self):
        """Test that updating with valid email formats is accepted"""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example123.com",
            "test@sub.example.com",
        ]

        for valid_email in valid_emails:
            with self.subTest(email=valid_email):
                data = self.valid_data.copy()
                data["email"] = valid_email

                response = self.client.put(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["email"], valid_email.lower())

    def test_update_user_with_empty_phone_number(self):
        """Test that updating with empty phone number is allowed"""
        data = self.valid_data.copy()
        data["phone_number"] = ""

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user_to_update.refresh_from_db()
        self.assertEqual(self.user_to_update.phone_number, "")

    def test_update_user_with_null_phone_number(self):
        """Test that updating with null phone number is allowed"""
        data = self.valid_data.copy()
        data["phone_number"] = None

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user_to_update.refresh_from_db()
        self.assertIsNone(self.user_to_update.phone_number)

    def test_update_user_email_case_insensitive_uniqueness(self):
        """Test that email uniqueness is case insensitive"""

        existing_user = User.objects.create_user(
            username="existinguser3",
            email="existing@example.com",
            password="Password123",
            role="user",
        )

        data = self.valid_data.copy()
        data["email"] = "EXISTING@EXAMPLE.COM"

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        if "error" in response.data:

            if isinstance(response.data["error"], str):

                self.assertIn("integrity", response.data["error"].lower())
            else:
                self.assertIn("email", response.data["error"])
                self.assertIn(
                    "A user with this email already exists",
                    str(response.data["error"]["email"]),
                )
        else:
            self.assertIn("email", response.data)
            self.assertIn(
                "A user with this email already exists", str(response.data["email"])
            )

    def test_update_user_email_whitespace_handling(self):
        """Test that email whitespace is properly handled"""
        data = self.valid_data.copy()
        data["email"] = "  test.whitespace@example.com  "

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["email"], "test.whitespace@example.com")

    def test_update_user_phone_whitespace_handling(self):
        """Test that phone number whitespace is properly handled"""
        data = self.valid_data.copy()
        data["phone_number"] = "  +1 234 567 8900  "

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["phone_number"], "+1 234 567 8900")

    def test_update_user_comprehensive_validation(self):
        """Test updating multiple fields with validation"""
        data = {
            "fullname": "Updated Full Name",
            "email": "updated@example.com",
            "phone_number": "+1-555-123-4567",
            "role": "admin",
        }

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fullname"], data["fullname"])
        self.assertEqual(response.data["email"], data["email"])
        self.assertEqual(response.data["phone_number"], data["phone_number"])
        self.assertEqual(response.data["role"], data["role"])

        self.user_to_update.refresh_from_db()
        self.assertEqual(self.user_to_update.fullname, data["fullname"])
        self.assertEqual(self.user_to_update.email, data["email"])
        self.assertEqual(self.user_to_update.phone_number, data["phone_number"])
        self.assertEqual(self.user_to_update.role, data["role"])

    def test_update_user_phone_number_max_length(self):
        """Test that phone number respects max length constraint"""

        data = self.valid_data.copy()
        data["phone_number"] = "123456789012345"

        response = self.client.put(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data["phone_number"] = "1234567890123456"
        response = self.client.put(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        if "error" in response.data:
            self.assertIn("phone_number", response.data["error"])
        else:
            self.assertIn("phone_number", response.data)

    def test_update_user_phone_number_minimum_digits(self):
        """Test phone number minimum digit requirement"""

        data = self.valid_data.copy()
        data["phone_number"] = "123456"

        response = self.client.put(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        if "error" in response.data:
            self.assertIn("phone_number", response.data["error"])
            self.assertIn(
                "at least 7 digits", str(response.data["error"]["phone_number"])
            )
        else:
            self.assertIn("phone_number", response.data)
            self.assertIn("at least 7 digits", str(response.data["phone_number"]))

        data["phone_number"] = "1234567"
        response = self.client.put(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_email_normalization(self):
        """Test that email is properly normalized to lowercase"""
        data = self.valid_data.copy()
        data["email"] = "TEST.EMAIL@EXAMPLE.COM"

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["email"], "test.email@example.com")

        self.user_to_update.refresh_from_db()
        self.assertEqual(self.user_to_update.email, "test.email@example.com")

    def test_update_user_partial_update(self):
        """Test that partial updates work correctly"""

        data = {"fullname": "Only Fullname Updated"}
        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fullname"], "Only Fullname Updated")

        self.user_to_update.refresh_from_db()
        self.assertEqual(self.user_to_update.email, "testuser@example.com")
        self.assertEqual(self.user_to_update.role, "user")

    def test_update_user_concurrent_email_update(self):
        """Test handling of concurrent email updates"""

        user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="Password123",
            role="user",
        )
        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="Password123",
            role="user",
        )

        url1 = reverse("update-user", kwargs={"pk": user1.pk})
        data = {"email": user2.email}

        response = self.client.put(url1, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        if "error" in response.data:
            self.assertIn("email", response.data["error"])
        else:
            self.assertIn("email", response.data)
