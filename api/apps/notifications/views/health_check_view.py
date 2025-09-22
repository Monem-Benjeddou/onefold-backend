"""
Health Check View

Simple health check endpoint for notifications service monitoring.
No authentication required for monitoring purposes.
"""

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ..models import Notification


@extend_schema(
    tags=["notifications"],
    summary="Health check for notifications service",
    description="""
    Health check endpoint for monitoring the notifications service status.

    **Features**:
    - No authentication required (public endpoint)
    - Returns service status and current timestamp
    - Used by monitoring systems and load balancers
    - Lightweight endpoint for service availability checks

    **Response Example**:
    ```json
    {
        "status": "healthy",
        "service": "notifications",
        "timestamp": "2023-12-01T12:00:00.000Z"
    }
    ```

    **Use Cases**:
    - Service health monitoring
    - Load balancer health checks
    - Uptime monitoring systems
    - Service discovery health validation
    """,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Service health status"},
                "service": {"type": "string", "description": "Service name identifier"},
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Current server timestamp",
                },
            },
        }
    },
)
@api_view(["GET"])
def health_check(request):
    """
    Health check endpoint for notifications service.

    Returns service status and timestamp for monitoring purposes.
    No authentication required to allow external monitoring systems.

    Response format:
    {
        "status": "healthy",
        "service": "notifications",
        "timestamp": "2023-12-01T12:00:00.000Z"
    }
    """
    return Response(
        {
            "status": "healthy",
            "service": "notifications",
            "timestamp": timezone.now().isoformat(),
        }
    )
