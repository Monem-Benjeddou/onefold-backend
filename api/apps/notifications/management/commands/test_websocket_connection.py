"""
Django Management Command: Test WebSocket Connection

Production-ready command to test WebSocket notification connections
with comprehensive validation and reporting.
"""

import asyncio
import json
import time
import websockets
from typing import Dict, Any, List
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.notifications.utils import NotificationSender

User = get_user_model()


class Command(BaseCommand):
    help = "Test WebSocket notification connections and system functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            type=str,
            default="localhost",
            help="WebSocket server host (default: localhost)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8000,
            help="WebSocket server port (default: 8000)",
        )
        parser.add_argument(
            "--protocol",
            type=str,
            default="ws",
            choices=["ws", "wss"],
            help="WebSocket protocol (default: ws)",
        )
        parser.add_argument(
            "--username",
            type=str,
            help="Username to test with (will create test user if not exists)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Connection timeout in seconds (default: 30)",
        )
        parser.add_argument(
            "--test-notifications",
            action="store_true",
            help="Test sending notifications through the system",
        )
        parser.add_argument(
            "--test-all-endpoints",
            action="store_true",
            help="Test all WebSocket endpoints (user, admin, public)",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Verbose output with detailed logs"
        )

    def handle(self, *args, **options):
        self.verbosity = options.get("verbosity", 1)
        self.verbose = options.get("verbose", False)

        host = options["host"]
        port = options["port"]
        protocol = options["protocol"]
        timeout = options["timeout"]

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🚀 Starting WebSocket Notification System Test\n"
                f"Target: {protocol}://{host}:{port}\n"
                f"Timeout: {timeout}s\n"
            )
        )

        try:

            self.test_basic_connectivity(host, port, protocol, timeout)

            if options["test_all_endpoints"]:
                asyncio.run(self.test_all_endpoints(host, port, protocol, timeout))
            else:

                test_user = self.get_or_create_test_user(options.get("username"))
                asyncio.run(
                    self.test_user_connection(host, port, protocol, timeout, test_user)
                )

            if options["test_notifications"]:
                self.test_notification_system()

            self.stdout.write(
                self.style.SUCCESS("\n✅ All WebSocket tests completed successfully!")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ WebSocket test failed: {str(e)}"))
            raise CommandError(f"WebSocket test failed: {str(e)}")

    def test_basic_connectivity(
        self, host: str, port: int, protocol: str, timeout: int
    ):
        """Test basic network connectivity to the WebSocket server."""
        self.stdout.write("\n📡 Testing basic connectivity...")

        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))

                if result == 0:
                    self.stdout.write(
                        self.style.SUCCESS("   ✓ TCP connection successful")
                    )
                else:
                    raise ConnectionError(f"Cannot connect to {host}:{port}")

        except Exception as e:
            raise CommandError(f"Basic connectivity test failed: {str(e)}")

    async def test_all_endpoints(
        self, host: str, port: int, protocol: str, timeout: int
    ):
        """Test all WebSocket endpoints."""
        self.stdout.write("\n🔌 Testing all WebSocket endpoints...")

        endpoints = [
            ("public", f"{protocol}://{host}:{port}/ws/notifications/public/"),
            ("user", f"{protocol}://{host}:{port}/ws/notifications/user/"),
            ("admin", f"{protocol}://{host}:{port}/ws/notifications/admin/"),
        ]

        results = {}

        for endpoint_type, url in endpoints:
            try:
                self.stdout.write(f"\n   Testing {endpoint_type} endpoint...")
                result = await self.test_websocket_endpoint(url, timeout, endpoint_type)
                results[endpoint_type] = result

                if result["success"]:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✓ {endpoint_type} endpoint working")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'   ⚠ {endpoint_type} endpoint failed: {result["error"]}'
                        )
                    )

            except Exception as e:
                results[endpoint_type] = {"success": False, "error": str(e)}
                self.stdout.write(
                    self.style.ERROR(f"   ❌ {endpoint_type} endpoint error: {str(e)}")
                )

        successful = sum(1 for r in results.values() if r["success"])
        total = len(results)

        self.stdout.write(
            f"\n📊 Endpoint Test Summary: {successful}/{total} successful"
        )

        if successful == 0:
            raise CommandError("No WebSocket endpoints are working")

    async def test_user_connection(
        self, host: str, port: int, protocol: str, timeout: int, user
    ):
        """Test user-specific WebSocket connection."""
        self.stdout.write(f"\n👤 Testing user connection for: {user.username}")

        url = f"{protocol}://{host}:{port}/ws/notifications/user/"

        try:
            result = await self.test_websocket_endpoint(url, timeout, "user", user)

            if result["success"]:
                self.stdout.write(
                    self.style.SUCCESS("   ✓ User WebSocket connection successful")
                )

                await self.test_ping_pong(url, timeout)

            else:
                raise ConnectionError(f'User connection failed: {result["error"]}')

        except Exception as e:
            raise CommandError(f"User connection test failed: {str(e)}")

    async def test_websocket_endpoint(
        self, url: str, timeout: int, endpoint_type: str, user=None
    ) -> Dict[str, Any]:
        """Test a specific WebSocket endpoint."""

        try:
            if self.verbose:
                self.stdout.write(f"      Connecting to: {url}")

            async with websockets.connect(
                url, timeout=timeout, ping_interval=None, ping_timeout=None
            ) as websocket:

                start_time = time.time()
                connection_established = False

                try:
                    while time.time() - start_time < 5:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)

                        if self.verbose:
                            self.stdout.write(f"      Received: {data}")

                        if data.get("type") == "connection_established":
                            connection_established = True
                            break

                except asyncio.TimeoutError:
                    pass

                ping_success = await self.send_ping_test(websocket)

                return {
                    "success": True,
                    "connection_established": connection_established,
                    "ping_success": ping_success,
                    "endpoint_type": endpoint_type,
                }

        except websockets.exceptions.ConnectionClosed as e:
            return {
                "success": False,
                "error": f"Connection closed: {e.code} {e.reason}",
                "connection_established": False,
                "ping_success": False,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "connection_established": False,
                "ping_success": False,
            }

    async def send_ping_test(self, websocket) -> bool:
        """Test sending ping message and receiving pong."""
        try:
            ping_message = {"type": "ping", "timestamp": time.time()}
            await websocket.send(json.dumps(ping_message))

            if self.verbose:
                self.stdout.write(f"      Sent ping: {ping_message}")

            start_time = time.time()
            while time.time() - start_time < 3:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)

                    if self.verbose:
                        self.stdout.write(f"      Received: {data}")

                    if data.get("type") == "pong":
                        return True

                except asyncio.TimeoutError:
                    continue

            return False

        except Exception as e:
            if self.verbose:
                self.stdout.write(f"      Ping test error: {str(e)}")
            return False

    async def test_ping_pong(self, url: str, timeout: int):
        """Test ping/pong functionality."""
        self.stdout.write("   🏓 Testing ping/pong...")

        try:
            async with websockets.connect(url, timeout=timeout) as websocket:
                ping_success = await self.send_ping_test(websocket)

                if ping_success:
                    self.stdout.write(self.style.SUCCESS("   ✓ Ping/pong working"))
                else:
                    self.stdout.write(self.style.WARNING("   ⚠ Ping/pong not working"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Ping/pong test failed: {str(e)}")
            )

    def test_notification_system(self):
        """Test the notification sending system."""
        self.stdout.write("\n📧 Testing notification system...")

        try:

            test_user = self.get_or_create_test_user()

            self.stdout.write("   Testing single notification...")
            notification = NotificationSender.send_notification(
                user=test_user,
                title="Test Notification",
                body="This is a test notification from the management command",
                notification_type="test",
                metadata={"test": True},
            )

            if notification:
                self.stdout.write(
                    self.style.SUCCESS("   ✓ Single notification sent successfully")
                )
            else:
                self.stdout.write(self.style.WARNING("   ⚠ Single notification failed"))

            self.stdout.write("   Testing bulk notifications...")
            test_users = list(User.objects.filter(is_staff=True)[:3])
            if test_users:
                results = NotificationSender.send_bulk_notifications(
                    users=test_users,
                    title="Bulk Test Notification",
                    body="This is a bulk test notification",
                    notification_type="bulk_test",
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'   ✓ Bulk notifications: {results["success"]} success, {results["failed"]} failed'
                    )
                )

            self.stdout.write("   Testing admin notifications...")
            admin_results = NotificationSender.send_admin_notification(
                title="Admin Test Notification",
                body="This is an admin test notification",
                notification_type="admin_test",
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'   ✓ Admin notifications: {admin_results["success"]} success, {admin_results["failed"]} failed'
                )
            )

            self.stdout.write("   Testing public notifications...")
            public_success = NotificationSender.send_public_notification(
                title="Public Test Notification",
                body="This is a public test notification",
                notification_type="public_test",
            )

            if public_success:
                self.stdout.write(
                    self.style.SUCCESS("   ✓ Public notification sent successfully")
                )
            else:
                self.stdout.write(self.style.WARNING("   ⚠ Public notification failed"))

        except Exception as e:
            raise CommandError(f"Notification system test failed: {str(e)}")

    def get_or_create_test_user(self, username=None):
        """Get or create a test user for testing."""
        username = username or "websocket_test_user"

        try:
            user = User.objects.get(username=username)
            if self.verbose:
                self.stdout.write(f"   Using existing test user: {username}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@test.com",
                password="testpassword123",
            )
            if self.verbose:
                self.stdout.write(f"   Created test user: {username}")

        return user

    def generate_test_report(self, results: Dict[str, Any]):
        """Generate a comprehensive test report."""
        self.stdout.write("\n📋 Test Report")
        self.stdout.write("=" * 50)

        for test_name, result in results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            self.stdout.write(f"{test_name}: {status}")

            if not result.get("success", False) and "error" in result:
                self.stdout.write(f'   Error: {result["error"]}')

            if "details" in result:
                for detail in result["details"]:
                    self.stdout.write(f"   - {detail}")

        self.stdout.write("=" * 50)
