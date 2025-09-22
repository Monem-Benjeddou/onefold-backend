"""
Production-Ready Notification Consumer Tests

Comprehensive test suite covering JWT authentication, Redis fallback,
WebSocket functionality, and error handling scenarios.
"""

import json
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings

from config.asgi import application
from apps.notifications.models import Notification

User = get_user_model()


TEST_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
class NotificationConsumerTest(TransactionTestCase):
    """
    Test the unified notification consumer with comprehensive scenarios.
    """

    @database_sync_to_async
    def create_user(
        self, username, email, password, is_staff=False, is_superuser=False
    ):
        """Create a test user with optional admin privileges."""
        user = User.objects.create(
            username=username, email=email, is_staff=is_staff, is_superuser=is_superuser
        )
        user.set_password(password)
        user.save()
        return user

    def generate_jwt_token(self, user, expired=False):
        """Generate a valid JWT token for testing."""
        exp_time = (
            datetime.utcnow() - timedelta(hours=1)
            if expired
            else datetime.utcnow() + timedelta(hours=1)
        )
        payload = {
            "token_type": "access",
            "exp": exp_time,
            "iat": datetime.utcnow(),
            "jti": "test-jti-123",
            "user_id": str(user.id),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    @database_sync_to_async
    def create_notification(self, title, user=None, body=None):
        """Create a test notification."""
        notification = Notification.objects.create(
            title=title,
            body=body,
            user=user,
        )
        return notification

    async def test_connect_without_token_anonymous(self):
        """Test that anonymous users can connect without a token."""
        communicator = WebsocketCommunicator(application, "/ws/notifications/")

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected, "Anonymous user should be able to connect")

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertFalse(response["is_authenticated"])
            self.assertIn("notifications_public", response["groups"])

        finally:
            await communicator.disconnect()

    async def test_connect_with_valid_jwt_token(self):
        """Test connection with a valid JWT token."""
        user = await self.create_user("testuser", "test@example.com", "testpass")
        token = self.generate_jwt_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected, "User with valid JWT should connect")

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertTrue(response["is_authenticated"])
            self.assertEqual(response["username"], user.username)
            self.assertEqual(response["user_id"], str(user.id))

            expected_groups = {
                "notifications_public",
                f"user_{user.id}",
                "notifications_authenticated",
            }
            self.assertTrue(expected_groups.issubset(set(response["groups"])))

        finally:
            await communicator.disconnect()

    async def test_connect_with_invalid_jwt_token(self):
        """Test connection with an invalid JWT token falls back to anonymous."""
        invalid_token = "invalid.jwt.token"

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={invalid_token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(
                connected, "Should connect as anonymous user with invalid token"
            )

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertFalse(
                response["is_authenticated"], "Should be anonymous with invalid token"
            )

        finally:
            await communicator.disconnect()

    async def test_connect_with_expired_jwt_token(self):
        """Test connection with an expired JWT token falls back to anonymous."""
        user = await self.create_user("testuser2", "test2@example.com", "testpass")
        expired_token = self.generate_jwt_token(user, expired=True)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={expired_token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(
                connected, "Should connect as anonymous user with expired token"
            )

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertFalse(
                response["is_authenticated"], "Should be anonymous with expired token"
            )

        finally:
            await communicator.disconnect()

    async def test_admin_user_privileges(self):
        """Test that admin users get proper groups and privileges."""
        admin_user = await self.create_user(
            "admin", "admin@example.com", "adminpass", is_staff=True, is_superuser=True
        )
        token = self.generate_jwt_token(admin_user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertTrue(response["is_authenticated"])
            self.assertTrue(response["is_admin"])

            admin_groups = {"notifications_admin", "notifications_superadmin"}
            self.assertTrue(admin_groups.issubset(set(response["groups"])))

        finally:
            await communicator.disconnect()

    async def test_ping_pong_functionality(self):
        """Test ping/pong for connection health checking."""
        user = await self.create_user("pinguser", "ping@example.com", "testpass")
        token = self.generate_jwt_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            await communicator.receive_json_from(timeout=5)

            await communicator.send_json_to({"type": "ping"})

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "pong")
            self.assertIn("timestamp", response)
            self.assertIn("server_time", response)

        finally:
            await communicator.disconnect()

    async def test_authentication_required_endpoints(self):
        """Test that certain endpoints require authentication."""

        communicator = WebsocketCommunicator(application, "/ws/notifications/")

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            await communicator.receive_json_from(timeout=5)

            await communicator.send_json_to({"type": "get_unread_count"})

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "error")
            self.assertEqual(response["code"], "auth_required")

        finally:
            await communicator.disconnect()

    async def test_authenticated_user_unread_count(self):
        """Test unread count functionality for authenticated users."""
        user = await self.create_user("countuser", "count@example.com", "testpass")
        token = self.generate_jwt_token(user)

        await self.create_notification("Test notification", user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            await communicator.receive_json_from(timeout=5)

            await communicator.send_json_to({"type": "get_unread_count"})

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "unread_count")
            self.assertIn("count", response)
            self.assertIsInstance(response["count"], int)

        finally:
            await communicator.disconnect()

    async def test_invalid_message_handling(self):
        """Test handling of invalid messages."""
        user = await self.create_user("invaliduser", "invalid@example.com", "testpass")
        token = self.generate_jwt_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            await communicator.receive_json_from(timeout=5)

            await communicator.send_json_to({"invalid": "message"})

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "error")
            self.assertEqual(response["code"], "missing_type")

        finally:
            await communicator.disconnect()

    async def test_connection_info_endpoint(self):
        """Test the get_connection_info endpoint."""
        user = await self.create_user("infouser", "info@example.com", "testpass")
        token = self.generate_jwt_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            await communicator.receive_json_from(timeout=5)

            await communicator.send_json_to({"type": "get_connection_info"})

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_info")
            self.assertEqual(response["username"], user.username)
            self.assertTrue(response["is_authenticated"])
            self.assertIn("groups", response)
            self.assertIn("connection_time", response)

        finally:
            await communicator.disconnect()

    @patch("apps.notifications.consumers.notification_consumer_utils.cache")
    async def test_rate_limiting(self, mock_cache):
        """Test rate limiting functionality."""

        mock_cache.get.return_value = 15
        mock_cache.set.return_value = None

        user = await self.create_user("rateuser", "rate@example.com", "testpass")
        token = self.generate_jwt_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            await communicator.receive_json_from(timeout=5)

            await communicator.send_json_to({"type": "ping"})

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "error")
            self.assertEqual(response["code"], "rate_limit")

        finally:
            await communicator.disconnect()

    @patch("apps.notifications.consumers.logger")
    async def test_redis_connection_failure_graceful_handling(self, mock_logger):
        """Test that WebSocket connections work even when Redis is unavailable."""

        user = await self.create_user("redisuser", "redis@example.com", "testpass")
        token = self.generate_jwt_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected, "Should connect even with Redis issues")

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertTrue(response["is_authenticated"])

            await communicator.send_json_to({"type": "ping"})
            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "pong")

        finally:
            await communicator.disconnect()


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
class NotificationConsumerEdgeCasesTest(TransactionTestCase):
    """
    Test edge cases and error scenarios for the notification consumer.
    """

    @database_sync_to_async
    def create_user(self, username, email, password):
        """Create a test user."""
        user = User.objects.create(username=username, email=email)
        user.set_password(password)
        user.save()
        return user

    def generate_jwt_token(self, user):
        """Generate a valid JWT token."""
        payload = {
            "token_type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "jti": "test-jti-123",
            "user_id": str(user.id),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    async def test_malformed_jwt_token(self):
        """Test handling of malformed JWT tokens."""
        malformed_token = "not.a.valid.jwt.token.format"

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={malformed_token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(
                connected, "Should connect as anonymous with malformed token"
            )

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertFalse(response["is_authenticated"])

        finally:
            await communicator.disconnect()

    async def test_jwt_with_invalid_user_id(self):
        """Test JWT token with non-existent user ID."""

        payload = {
            "token_type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "jti": "test-jti-123",
            "user_id": "00000000-0000-0000-0000-000000000000",
        }
        invalid_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={invalid_token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(
                connected, "Should connect as anonymous with invalid user ID"
            )

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "connection_established")
            self.assertFalse(response["is_authenticated"])

        finally:
            await communicator.disconnect()

    async def test_concurrent_connections_same_user(self):
        """Test multiple connections from the same user."""
        user = await self.create_user(
            "concurrentuser", "concurrent@example.com", "testpass"
        )
        token = self.generate_jwt_token(user)

        comm1 = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        comm2 = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")

        try:

            connected1, _ = await comm1.connect()
            connected2, _ = await comm2.connect()

            self.assertTrue(connected1)
            self.assertTrue(connected2)

            resp1 = await comm1.receive_json_from(timeout=5)
            resp2 = await comm2.receive_json_from(timeout=5)

            self.assertEqual(resp1["type"], "connection_established")
            self.assertEqual(resp2["type"], "connection_established")
            self.assertEqual(resp1["user_id"], resp2["user_id"])

        finally:
            await comm1.disconnect()
            await comm2.disconnect()

    async def test_unknown_message_type(self):
        """Test handling of unknown message types."""
        user = await self.create_user("unknownuser", "unknown@example.com", "testpass")
        token = self.generate_jwt_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )

        try:
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            await communicator.receive_json_from(timeout=5)

            await communicator.send_json_to({"type": "unknown_message_type"})

            response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(response["type"], "error")
            self.assertEqual(response["code"], "unknown_type")

        finally:
            await communicator.disconnect()
