"""
Django settings initialization.
This module determines which settings file to use based on the environment.

The settings are organized in a modular way:
- Base settings are in base.py
- Environment-specific settings are in development.py and production.py
- Component-specific settings are in the components directory

To use a specific environment, set the ENV environment variable to:
- 1 for development (default)
- 0 for production
"""

import os


environment = os.environ.get("ENV", "1")
LOGIN_REDIRECT_URL = "/admin/dashboard/"

if environment == "0":
    from .production import *
else:
    from .development import *
