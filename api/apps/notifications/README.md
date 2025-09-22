# Notifications App

A modular Django REST Framework application for managing user notifications with real-time WebSocket support.

## Architecture Overview

The notifications app has been refactored following Django best practices with a modular structure:

```
apps/notifications/
├── views/
│   ├── __init__.py
│   ├── notification_list.py      # GET /notifications/
│   ├── notification_detail.py    # GET /notifications/{id}/
│   ├── notification_create.py    # POST /notifications/create/
│   ├── notification_update.py    # PATCH/PUT /notifications/{id}/update/
│   └── notification_delete.py    # DELETE /notifications/{id}/delete/
├── serializers/
│   ├── __init__.py
│   ├── notification_list.py      # List serializer
│   ├── notification_detail.py    # Detail serializer
│   ├── notification_create.py    # Create serializer
│   └── notification_update.py    # Update serializer
├── tests/
│   ├── views/
│   │   └── test_notification_*.py
│   ├── serializers/
│   │   └── test_notification_*.py
│   └── constants.py
├── models.py
├── permissions.py
├── signals.py
├── consumers.py
├── routing.py
└── urls.py
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/api/v1/notifications/` | List user notifications | 60/min |
| POST | `/api/v1/notifications/create/` | Create notification | 10/min |
| GET | `/api/v1/notifications/{id}/` | Get notification detail | 120/min |
| PATCH/PUT | `/api/v1/notifications/{id}/update/` | Update notification status | 30/min |
| DELETE | `/api/v1/notifications/{id}/delete/` | Delete notification | 20/min |
| POST | `/api/v1/notifications/mark-all-read/` | Mark all as read | 5/min |

### Legacy Endpoints (Backward Compatibility)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications/notifications/` | Legacy list endpoint |
| GET | `/api/v1/notifications/notifications/{id}/` | Legacy detail endpoint |

## Features

### Security & Performance
- **Authentication Required**: All endpoints require user authentication
- **Rate Limiting**: Different rate limits per endpoint type
- **API Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Permission Validation**: Users can only access their own notifications
- **Input Validation**: Comprehensive validation for all input fields

### Filtering & Pagination
- **Status Filtering**: Filter by `unread`, `read`, or `all` notifications
- **Pagination**: MetaPageNumberPagination with customizable page size
- **Ordering**: Sort by creation date, update date (newest first by default)

### Real-time Features
- **WebSocket Support**: Real-time notification delivery via Django Channels
- **Signal Integration**: Automatic WebSocket notifications on creation
- **User-specific Channels**: Private notification channels per user

## Usage Examples

### List Notifications
```bash
# Get unread notifications (default)
GET /api/v1/notifications/
Authorization: Bearer <token>

# Get all notifications
GET /api/v1/notifications/?status=all

# Get read notifications only
GET /api/v1/notifications/?status=read

# Paginated results
GET /api/v1/notifications/?page=2&limit=10
```

### Create Notification
```bash
POST /api/v1/notifications/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "title": "New Notification",
    "body": "This is a test notification",
    "user": 1
}
```

### Update Notification Status
```bash
PATCH /api/v1/notifications/123/update/
Authorization: Bearer <token>
Content-Type: application/json

{
    "status": "r"  # Mark as read
}
```

### Mark All as Read
```bash
POST /api/v1/notifications/mark-all-read/
Authorization: Bearer <token>
```

## Testing

### Running Tests

```bash
# Run all notification tests
make test-file path=apps.notifications.tests

# Run specific test modules
make test-file path=apps.notifications.tests.test_basic

# Run individual test cases
python manage.py test apps.notifications.tests.test_basic.NotificationBasicTestCase.test_imports_work
```

### Test Structure

Tests are organized by functionality:
- `test_basic.py` - Basic functionality and imports
- `views/test_notification_*.py` - View-specific tests
- `serializers/test_notification_*.py` - Serializer-specific tests

## Models

### Notification Model

```python
class Notification(AbstractModelTimeStamp):
    MARKED_READ = "r"
    MARKED_UNREAD = "u"
    
    user = ForeignKey(User)           # Notification recipient
    title = CharField(max_length=250) # Notification title
    body = TextField()                # Notification content
    status = CharField(choices=...)   # Read/unread status
    created = DateTimeField()         # Auto-generated
    updated = DateTimeField()         # Auto-generated
```

## Serializers

### NotificationListSerializer
- **Purpose**: Optimized for list views
- **Fields**: `id`, `title`, `body`, `status`, `created`
- **Features**: Performance-optimized, minimal fields

### NotificationDetailSerializer
- **Purpose**: Complete notification information
- **Fields**: `id`, `user`, `title`, `body`, `status`, `created`, `updated`
- **Features**: Full notification details

### NotificationCreateSerializer
- **Purpose**: Notification creation with validation
- **Fields**: `title`, `body`, `user`
- **Validation**: Title length, body length, required fields

### NotificationUpdateSerializer
- **Purpose**: Status updates (read/unread)
- **Fields**: `status`
- **Validation**: Valid status choices only

## WebSocket Integration

### Real-time Notifications

The app includes WebSocket support for real-time notification delivery:

```javascript
// Frontend WebSocket connection
const socket = new WebSocket('ws://localhost:8009/ws/notifications/');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('New notification:', data);
};
```

### Consumer Groups
- **User-specific**: `user_{user_id}_notifications_group`
- **Public**: `public_notifications_group` (for system-wide notifications)

## Migration Guide

### From Legacy Structure

The refactoring maintains backward compatibility:

```python
# Old imports (still work)
from apps.notifications.views import NotificationAPIView
from apps.notifications.serializers import NotificationMiniSerializer

# New imports (recommended)
from apps.notifications.views import NotificationDetailView
from apps.notifications.serializers import NotificationListSerializer
```

### Legacy Aliases
- `NotificationAPIView` → `NotificationDetailView`
- `MarkedAllAsReadNotificationView` → `NotificationMarkAllReadView`
- `NotificationMiniSerializer` → `NotificationListSerializer`
- `NotificationSerializer` → `NotificationDetailSerializer`

## Best Practices

### Error Handling
All views use the `@api_error_handler` decorator for consistent error responses.

### Rate Limiting
Different endpoints have appropriate rate limits:
- **List/Detail**: Higher limits for read operations
- **Create**: Lower limits to prevent spam
- **Bulk operations**: Very low limits for expensive operations

### Security
- **Authentication**: Required for all endpoints
- **Authorization**: Users can only access their own notifications
- **Input Validation**: Comprehensive validation on all inputs

### Performance
- **Pagination**: All list endpoints are paginated
- **Field Selection**: Minimal fields in list views
- **Database Optimization**: Efficient queries with proper indexing
- **Caching**: WebSocket channel layer caching

## Dependencies

- Django REST Framework
- Django Channels (for WebSocket support)
- django-ratelimit (for rate limiting)
- drf-spectacular (for API documentation)

## Configuration

### Settings
```python
# Rate limiting
RATE_LIMITER_ENABLED = True

# WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### URL Configuration
```python
# config/urls.py
path("api/v1/notifications/", include("apps.notifications.urls")),
```

## Contributing

When adding new features:

1. **Follow the modular structure**: Separate files for each action
2. **Add comprehensive tests**: Cover all new functionality
3. **Use proper decorators**: `@api_error_handler` and `@dynamic_rate_limit`
4. **Document API changes**: Update this README and API documentation
5. **Maintain backward compatibility**: Use aliases for breaking changes 