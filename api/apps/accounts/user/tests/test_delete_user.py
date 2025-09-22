import pytest
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.accounts.user.models import User
from apps.accounts.user.tests.factories import UserFactory


@override_settings(RATE_LIMITER_ENABLED=False)
class DeleteUserViewTest(TestCase):
    """Test cases for the DeleteUserView"""

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

        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="Password123",
            role="user",
        )

        self.user_to_delete = User.objects.create_user(
            username="deleteuser",
            email="delete@example.com",
            password="Password123",
            role="user",
        )

    def test_admin_can_delete_user(self):
        """Test that admin users can delete other users"""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("delete-user", kwargs={"pk": self.user_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user_to_delete.pk).exists())

    def test_regular_user_cannot_delete_user(self):
        """Test that regular users cannot delete other users"""
        self.client.force_authenticate(user=self.regular_user)

        url = reverse("delete-user", kwargs={"pk": self.user_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(pk=self.user_to_delete.pk).exists())

    def test_unauthenticated_user_cannot_delete_user(self):
        """Test that unauthenticated users cannot delete users"""
        url = reverse("delete-user", kwargs={"pk": self.user_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(pk=self.user_to_delete.pk).exists())

    def test_delete_nonexistent_user(self):
        """Test deleting a user that doesn't exist"""
        self.client.force_authenticate(user=self.admin_user)

        import uuid

        url = reverse("delete-user", kwargs={"pk": uuid.uuid4()})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
