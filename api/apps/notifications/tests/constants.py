"""
Test constants for notifications app tests.
"""

TEST_NOTIFICATION_DATA = {
    "title": "Test Notification",
    "body": "This is a test notification body",
    "status": "u",
}

TEST_NOTIFICATION_UPDATE_DATA = {
    "status": "r",
}


NOTIFICATIONS_LIST_URL = "/api/v1/notifications/"
NOTIFICATION_DETAIL_URL = "/api/v1/notifications/{id}/"
NOTIFICATION_UPDATE_URL = "/api/v1/notifications/{id}/"
NOTIFICATION_DELETE_URL = "/api/v1/notifications/{id}/"
NOTIFICATION_MARK_ALL_READ_URL = "/api/v1/notifications/mark-all-read/"


LEGACY_NOTIFICATIONS_LIST_URL = "/api/v1/notifications/notifications/"
LEGACY_NOTIFICATION_DETAIL_URL = "/api/v1/notifications/notifications/{id}/"


RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_PERIOD = 60


NOTIFICATION_STATUS_READ = "r"
NOTIFICATION_STATUS_UNREAD = "u"
