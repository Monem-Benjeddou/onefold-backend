from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterViewTest(APITestCase):
    @patch("core.tasks.sms.send_sms_task.delay")
    @patch("core.tasks.send_activation_email.delay")
    def test_register_basic_info(self, mock_email, mock_sms_task):
        from unittest.mock import MagicMock

        mock_sms_task.return_value = MagicMock()
        mock_email.return_value = None

        data = {
            "email": "testuser@example.com",
            "fullname": "Test User",
            "password": "securepassword",
            "phone_number": "+5000000001",
        }

        response = self.client.post(reverse("auth-register"), data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=data["email"])
        self.assertEqual(user.fullname, data["fullname"])
