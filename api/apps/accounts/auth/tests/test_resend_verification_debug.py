from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.apps import apps

from apps.accounts.user.models import VerificationCode

User = get_user_model()


class ResendVerificationCodeDebugTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            fullname="Test User",
            username="testuser",
        )
        self.user.save()

        self.test_country = apps.get_model("countries", "Country").objects.create(
            name="Test Country", iso2="TC", iso3="TCY"
        )

    def test_resend_verification_code_debug(self):
        """Debug test to see what's causing internal error"""
        url = "/api/v1/auth/resend-verification-code/"
        data = {"email": self.user.email}

        response = self.client.post(url, data)

        print(f"Status Code: {response.status_code}")
        print(f"Response Data: {response.json()}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_resend_verification_code_nonexistent_user(self):
        """Test with non-existent user"""
        url = "/api/v1/auth/resend-verification-code/"
        data = {"email": "nonexistent@example.com"}

        response = self.client.post(url, data)

        print(f"Status Code: {response.status_code}")
        print(f"Response Data: {response.json()}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
