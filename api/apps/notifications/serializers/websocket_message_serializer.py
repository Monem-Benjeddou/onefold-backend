"""
WebSocket Message Serializer

Base serializer for WebSocket messages with common fields.
Provides structure for real-time notification messaging.
"""

from django.utils import timezone
from rest_framework import serializers


class WebSocketMessageSerializer(serializers.Serializer):
    """
    Base serializer for WebSocket messages.

    Provides common fields for WebSocket communication:
    - type: Message type identifier
    - timestamp: Message timestamp (auto-generated)
    - user_id: Optional user identifier
    - session_id: Optional session identifier
    """

    type = serializers.CharField()
    timestamp = serializers.DateTimeField(default=timezone.now)
    user_id = serializers.IntegerField(required=False)
    session_id = serializers.CharField(required=False)
