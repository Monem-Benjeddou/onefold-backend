from rest_framework.exceptions import (
    NotFound,
    AuthenticationFailed,
    ValidationError,
)
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import (
    TokenAuthentication as BaseTokenAuthentication,
)


def flatten_validation_error(error_detail):
    """
    Flatten non_field_errors to a simple string while keeping other field errors as they are.
    """
    if isinstance(error_detail, dict):

        if len(error_detail) == 1 and "non_field_errors" in error_detail:
            non_field_errors = error_detail["non_field_errors"]
            if isinstance(non_field_errors, list) and len(non_field_errors) > 0:
                return str(non_field_errors[0])

        elif "non_field_errors" in error_detail:
            flattened = error_detail.copy()
            non_field_errors = flattened["non_field_errors"]
            if isinstance(non_field_errors, list) and len(non_field_errors) > 0:

                del flattened["non_field_errors"]

                if flattened:
                    flattened["error"] = str(non_field_errors[0])
                    return flattened
                else:

                    return str(non_field_errors[0])

    return error_detail


class CustomTokenAuthentication(BaseTokenAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if not result:
            raise AuthenticationFailed(
                {"error": "Authentication credentials were not provided."}
            )
        return result


def get_object_or_404(model, **kwargs):
    message = kwargs.pop("message", None)
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise NotFound("Object not found." if not message else message)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, AuthenticationFailed):
        custom_response_data = {"error": exc.detail}
        return Response(custom_response_data, status=status.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, ValidationError):
        flattened_error = flatten_validation_error(exc.detail)
        custom_response_data = {"error": flattened_error}
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, NotFound):
        custom_response_data = {"error": exc.detail}
        return Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)

    if response is not None:
        if isinstance(response.data, dict) and "detail" in response.data:
            custom_response_data = {"error": response.data["detail"]}
            response.data = custom_response_data

    return response
