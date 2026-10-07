"""
Root-level pytest configuration for Django.
"""

import os
import django
from django.conf import settings

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.config.pytest_settings')
# Some modules import config.settings helpers, which runs the settings package
# and requires DEBUG to be set explicitly.
os.environ.setdefault('DEBUG', '0')

# Configure Django
django.setup()
