"""
REST Framework settings for the project.
"""

import os
from ..config_loader import get_environment, get_api_config, get_frontend_config


SPECTACULAR_SETTINGS = {
    "TITLE": "Kolct API",
    "DESCRIPTION": "Kolct API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "COMPONENT_SPLIT_REQUEST": True,
    "OAUTH2_FLOWS": ["password"],
    "OAUTH2_SCOPES": {
        "read": "Read scope",
        "write": "Write scope",
    },
}


REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "api.core.exceptions.custom_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.CustomJWTAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "PAGE_SIZE": 10,
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"',
        }
    },
    "FORM_ENCTYPE": "multipart/form-data",
}


current_env = get_environment()
api_config = get_api_config()

if current_env == "development":
    SPECTACULAR_SETTINGS["SERVERS"] = [
        {
            "url": api_config["BASE_URL"],
            "description": "Development server",
        },
    ]
elif current_env == "production":
    SPECTACULAR_SETTINGS["SERVERS"] = [
        {
            "url": "https://api.kolct-api.neothons.com",
            "description": "Production server",
        },
        {
            "url": api_config["BASE_URL"],
            "description": "Local/Development server",
        },
    ]
else:
    SPECTACULAR_SETTINGS["SERVERS"] = [
        {
            "url": api_config["BASE_URL"],
            "description": f"{current_env.title()} server",
        },
    ]
