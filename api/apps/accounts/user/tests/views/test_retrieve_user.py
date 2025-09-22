from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from apps.accounts.user.models import User


class RetrieveUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="Password123",
            fullname="User One",
            role="user",
        )

        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="Password123",
            fullname="User Two",
            role="user",
        )

        self.url = reverse("retrieve-user", kwargs={"pk": self.user2.pk})

    def test_retrieve_user_public_access_success(self):
        """Test retrieving user details with public access (no authentication required)"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user2.id))
        self.assertEqual(response.data["email"], self.user2.email)
        self.assertEqual(response.data["fullname"], self.user2.fullname)
        self.assertEqual(response.data["username"], self.user2.username)

    def test_retrieve_user_unauthenticated(self):
        """Test that unauthenticated requests work (public access)"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user2.id))
        self.assertEqual(response.data["email"], self.user2.email)

    def test_retrieve_nonexistent_user(self):
        """Test retrieving a user that doesn't exist"""
        non_existent_url = reverse("retrieve-user", kwargs={"pk": uuid.uuid4()})

        response = self.client.get(non_existent_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "User not found.")

    def test_retrieve_user_response_format(self):
        """Test that the response contains expected user fields"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ["id", "email", "username", "fullname", "role", "_id"]
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_retrieve_own_user_details(self):
        """Test that a user can retrieve their own details (public access)"""
        own_url = reverse("retrieve-user", kwargs={"pk": self.user1.pk})
        response = self.client.get(own_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user1.id))
        self.assertEqual(response.data["email"], self.user1.email)

    def test_retrieve_user_public_access_no_auth(self):
        """Test that the endpoint works without any authentication (truly public)"""
        
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user2.id))
        self.assertEqual(response.data["email"], self.user2.email)
        self.assertEqual(response.data["fullname"], self.user2.fullname)
        self.assertEqual(response.data["username"], self.user2.username)
