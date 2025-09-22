"""
Custom schema generation hooks for DRF Spectacular to handle ManyToManyField issues.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.db import models


def spectacular_postprocessing_hook(result, generator, request, public):
    """
    Post-processing hook to handle schema generation issues.
    """
    # This hook can be used to modify the generated schema
    # if needed to handle specific ManyToManyField issues
    return result


def get_schema_hooks():
    """
    Get schema generation hooks for DRF Spectacular.
    """
    return [spectacular_postprocessing_hook]


def custom_preprocessing_filter(result, generator, request, public):
    """
    Preprocessing filter to handle problematic model fields before schema generation.
    """
    # This can be used to filter out problematic fields or models
    return result


def get_preprocessing_filters():
    """
    Get preprocessing filters for DRF Spectacular.
    """
    return [custom_preprocessing_filter]
