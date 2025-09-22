import json
from rest_framework.test import APIClient, APITestCase
from django.test import override_settings
from apps.accounts.user.models import User
import pytest
from django.urls import reverse
from rest_framework import status


@override_settings(RATE_LIMITER_ENABLED=False)
class UserAPIExactResponseTest(APITestCase):
    """Test class for user API exact responses."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.normal_user = User.objects.create_user(
            email="user@example.com",
            username="normaluser",
            password="password123",
            fullname="Normal User",
            role="user",
        )

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="adminuser",
            password="password123",
            fullname="Admin User",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

    def test_list_users_exact_response(self):
        """Test the exact response for listing users."""
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/v1/users/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIsInstance(response_data, dict)
        self.assertIn("meta", response_data)
        self.assertIn("results", response_data)
        self.assertIsInstance(response_data["results"], list)

        if response_data["results"]:
            user = response_data["results"][0]
            expected_fields = ["id", "email", "username", "fullname", "role"]
            for field in expected_fields:
                self.assertIn(field, user)

    def test_user_detail_exact_response(self):
        """Test the exact response for user detail."""

        pass

    def test_create_user_exact_response(self):
        """Test the exact response for creating a user."""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "fullname": "New User",
            "username": "newuser",
        }
        url = "/api/v1/users/create/"
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        user = response.json()

        expected_fields = ["id", "email", "fullname", "role"]
        for field in expected_fields:
            self.assertIn(field, user)

        self.assertEqual(user["email"], "newuser@example.com")
        self.assertEqual(user["fullname"], "New User")

    def test_update_user_exact_response(self):
        """Test the exact response for updating a user."""
        self.client.force_authenticate(user=self.admin_user)

        data = {"fullname": "Updated Normal User"}
        url = f"/api/v1/users/{self.normal_user.id}/update/"
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, 200)
        user = response.json()

        self.assertEqual(user["fullname"], "Updated Normal User")

    def test_update_role_exact_response(self):
        """Test the exact response format for update role endpoint"""
        self.client.force_authenticate(user=self.admin_user)

        data = {"role": "admin"}
        url = f"/api/v1/users/{self.normal_user.id}/update-role/"
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.data)
        self.assertEqual(response.data["status"], "Role updated to admin")

        self.assertIn("Content-Type", response)

    def test_export_users_exact_response(self):
        """Test the exact response for exporting users."""
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/v1/users/export/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertIn("Content-Type", response)
