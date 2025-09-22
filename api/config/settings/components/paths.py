"""
Path configurations for the Django project.
"""

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


GEOIP_PATH = os.path.join(BASE_DIR, "geoip")
