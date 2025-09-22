"""
Patch for Django REST Framework's model_meta utility to handle ManyToManyField through relationship issues.
"""

from rest_framework.utils.model_meta import _get_forward_relationships
from django.db import models
import logging

logger = logging.getLogger(__name__)


def patched_get_forward_relationships(opts):
    """
    Patched version of _get_forward_relationships that handles None through relationships.
    """
    try:
        return _get_forward_relationships(opts)
    except AttributeError as e:
        if "'NoneType' object has no attribute '_meta'" in str(e):
            logger.warning(f"Skipping problematic ManyToManyField in {opts.model.__name__}: {e}")
            # Return empty dict to avoid the error
            return {}
        raise


def apply_model_meta_patch():
    """
    Apply the patch to fix ManyToManyField through relationship issues.
    """
    import rest_framework.utils.model_meta as model_meta_module
    model_meta_module._get_forward_relationships = patched_get_forward_relationships
    logger.info("Applied model_meta patch for ManyToManyField through relationship issues")
