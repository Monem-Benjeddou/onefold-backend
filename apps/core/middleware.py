import logging
import re
import uuid

logger = logging.getLogger("onefold.request")

# Accept an upstream id (from the web app or a load balancer) if it looks sane.
VALID_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestIDMiddleware:
    """
    Give every request an id, return it as ``X-Request-ID`` and put it in error
    bodies, so a builder can quote it to support and we can find the log line.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get("X-Request-ID", "")
        request.request_id = incoming if VALID_ID.match(incoming) else uuid.uuid4().hex
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        if response.status_code >= 500:
            logger.error(
                "%s %s -> %s [request_id=%s]",
                request.method,
                request.path,
                response.status_code,
                request.request_id,
            )
        return response
