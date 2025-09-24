"""
Root-level pytest configuration for Django.
"""

import os
import django
from django.conf import settings

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.config.pytest_settings')

# Configure Django
django.setup()
