"""
Custom schema generator to handle ManyToManyField issues with DRF Spectacular.
"""

from drf_spectacular.generators import SchemaGenerator
from rest_framework.utils.model_meta import get_field_info
from django.db import models
import logging

logger = logging.getLogger(__name__)


class CustomSchemaGenerator(SchemaGenerator):
    """
    Custom schema generator that handles ManyToManyField through relationship issues.
    """
    
    def _get_serializer_fields(self, serializer):
        """
        Override to handle ManyToManyField issues gracefully.
        """
        try:
            return super()._get_serializer_fields(serializer)
        except AttributeError as e:
            if "'NoneType' object has no attribute '_meta'" in str(e):
                logger.warning(f"Skipping problematic serializer fields for {serializer.__class__.__name__}: {e}")
                # Return empty fields to avoid the error
                return {}
            raise
    
    def _map_serializer(self, serializer, direction, bypass_extensions=False):
        """
        Override to handle ManyToManyField through relationship issues.
        """
        try:
            return super()._map_serializer(serializer, direction, bypass_extensions)
        except AttributeError as e:
            if "'NoneType' object has no attribute '_meta'" in str(e):
                logger.warning(f"Skipping problematic serializer mapping for {serializer.__class__.__name__}: {e}")
                # Return a basic schema to avoid the error
                return {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            raise


def safe_get_field_info(model):
    """
    Safely get field info for a model, handling ManyToManyField issues.
    """
    try:
        return get_field_info(model)
    except AttributeError as e:
        if "'NoneType' object has no attribute '_meta'" in str(e):
            logger.warning(f"Skipping problematic field info for {model.__class__.__name__}: {e}")
            # Return minimal field info
            return {
                'forward_relations': {},
                'reverse_relations': {},
                'fields_and_pk': {},
                'fields': {},
                'pk': model._meta.pk
            }
        raise
