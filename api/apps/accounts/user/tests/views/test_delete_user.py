from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import Group
import uuid

from apps.accounts.user.models import User


class DeleteUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_group, _ = Group.objects.get_or_create(name="Admin")

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
        )

        self.admin_user.groups.add(self.admin_group)

        self.user_to_delete = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Password123",
            fullname="Test User To Delete",
            role="user",
        )

        self.url = reverse("delete-user", kwargs={"pk": self.user_to_delete.pk})

        self.client.force_authenticate(user=self.admin_user)

    def test_delete_user_authenticated_as_admin(self):
        """Test deleting a user when authenticated as admin"""
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(User.objects.filter(pk=self.user_to_delete.pk).exists())

    def test_delete_nonexistent_user(self):
        """Test deleting a user that doesn't exist"""
        non_existent_url = reverse("delete-user", kwargs={"pk": uuid.uuid4()})

        response = self.client.delete(non_existent_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertTrue(User.objects.filter(pk=self.user_to_delete.pk).exists())

    def test_delete_user_as_regular_user(self):
        """Test that regular users cannot delete users"""
        regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="Password123",
            role="user",
        )
        self.client.force_authenticate(user=regular_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(User.objects.filter(pk=self.user_to_delete.pk).exists())
