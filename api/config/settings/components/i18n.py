"""
Internationalization settings for the project.
"""

import os
from django.utils.translation import gettext_lazy as _


LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "en-us")
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_I18N = True

USE_TZ = True


LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("es", _("Spanish")),
    ("ar", _("Arabic")),
    ("de", _("German")),
]


LOCALE_PATHS = [
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "locale",
    ),
]


DATE_FORMAT = "Y-m-d"
DATETIME_FORMAT = "Y-m-d H:i:s"
SHORT_DATE_FORMAT = "Y-m-d"
SHORT_DATETIME_FORMAT = "Y-m-d H:i"


FIRST_DAY_OF_WEEK = 1


I18N_DEV = {
    "LANGUAGE_CODE": "en-us",
    "TIME_ZONE": "UTC",
}


I18N_TEST = {
    "LANGUAGE_CODE": "en",
    "TIME_ZONE": "UTC",
}


I18N_PROD = {
    "LANGUAGE_CODE": LANGUAGE_CODE,
    "TIME_ZONE": TIME_ZONE,
}
