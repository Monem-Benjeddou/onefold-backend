from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """DRF's handler, plus the request id on every error body."""
    response = drf_exception_handler(exc, context)
    if response is None or not isinstance(response.data, dict):
        return response
    request = context.get("request")
    request_id = getattr(request, "request_id", None) or getattr(
        getattr(request, "_request", None), "request_id", None
    )
    if request_id:
        response.data["request_id"] = request_id
    detail = getattr(exc, "detail", None)
    if "code" not in response.data and isinstance(detail, str) and getattr(detail, "code", None):
        response.data["code"] = detail.code
    wait = getattr(exc, "wait", None)
    if wait is not None:
        response.data["retry_after"] = int(wait)
    return response
