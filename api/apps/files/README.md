# Files Module

This module handles file upload and management functionality following Django and DRF best practices.

## Architecture

The module has been refactored to follow a clean, modular architecture with separation of concerns:

### Directory Structure

```
apps/files/
├── views/
│   ├── __init__.py
│   ├── create.py          # File upload view (POST)
│   └── list.py            # File listing view (GET)
├── serializers/
│   ├── __init__.py
│   ├── create.py          # File creation serializer
│   └── retrieve.py        # File retrieval serializer
├── tests/
│   ├── views/
│   │   ├── test_create.py # Tests for file creation
│   │   └── test_list.py   # Tests for file listing
│   ├── serializers/
│   │   ├── test_create.py # Tests for create serializer
│   │   └── test_retrieve.py # Tests for retrieve serializer
│   ├── test_endpoints.py  # Legacy tests (backward compatibility)
│   └── constants.py       # Test constants
├── models.py              # File model
├── utils.py               # Utility functions
├── urls.py                # URL configuration
├── views.py               # Legacy imports (backward compatibility)
├── serializers.py         # Legacy imports (backward compatibility)
└── README.md              # This file
```

## Features

### File Upload (POST /api/v1/files/upload/)
- **View**: `FileCreateView`
- **Serializer**: `CreateFileSerializer`
- **Rate Limit**: 10 requests per minute
- **Authentication**: Required
- **Supported Formats**: pdf, docx, doc, xls, xlsx, csv, txt, png, jpg, jpeg, mp4, mp3

### File Listing (GET /api/v1/files/)
- **View**: `FileListView`
- **Serializer**: `FileSerializer`
- **Rate Limit**: 20 requests per minute
- **Authentication**: Required
- **Pagination**: MetaPageNumberPagination (5 items per page)
- **Ordering**: By creation date (newest first)

## API Endpoints

### Upload File
```http
POST /api/v1/files/upload/
Content-Type: multipart/form-data
Authorization: Bearer <token>

{
  "file": <file_data>
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "generated_filename.ext",
  "type": "application/pdf",
  "url": "/media/files/generated_filename.ext",
  "file": "http://domain.com/media/files/generated_filename.ext",
  "created": "2023-01-01T00:00:00Z",
  "updated": "2023-01-01T00:00:00Z"
}
```

### List Files
```http
GET /api/v1/files/
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "meta": {
    "count": 10,
    "next": "http://domain.com/api/v1/files/?page=2",
    "previous": null,
    "next_page_number": 2,
    "previous_page_number": null,
    "limit": 5,
    "total_pages": 2,
    "current_page_number": 1
  },
  "results": [
    {
      "id": "uuid",
      "name": "filename.ext",
      "type": "application/pdf",
      "url": "/media/files/filename.ext",
      "file": "http://domain.com/media/files/filename.ext",
      "created": "2023-01-01T00:00:00Z",
      "updated": "2023-01-01T00:00:00Z"
    }
  ]
}
```

## Security Features

### Rate Limiting
- **File Upload**: 10 requests per minute per IP
- **File Listing**: 20 requests per minute per IP
- Configurable via `RATE_LIMITER_ENABLED` setting
- Uses Django cache for tracking

### File Validation
- **Extension Validation**: Only allowed file types accepted
- **File Size**: Handled by Django's FileField
- **Authentication**: All endpoints require authentication

### Error Handling
- **API Error Handler**: Consistent error responses
- **Validation Errors**: Detailed field-level errors
- **Rate Limit Errors**: 429 Too Many Requests
- **Authentication Errors**: 401 Unauthorized

## File Type Detection

The module automatically detects file types based on extensions:

```python
# PDF files
"pdf" → "application/pdf"

# Documents
"doc", "docx" → "application/msword"
"xls", "xlsx" → "application/vnd.ms-excel"

# Images
"jpg", "jpeg", "png", "gif" → "image"

# Media
"mp4", "avi", "mkv", "webm" → "video"
"mp3", "wav", "flac", "ogg" → "audio"

# Default
* → "text"
```

## Testing

### Running Tests

```bash
# Run all file tests
make test-file path=api/apps/files/tests/

# Run specific test categories
make test-file path=api/apps/files/tests/views/test_create.py
make test-file path=api/apps/files/tests/views/test_list.py
make test-file path=api/apps/files/tests/serializers/test_create.py
make test-file path=api/apps/files/tests/serializers/test_retrieve.py

# Run legacy tests (backward compatibility)
make test-file path=api/apps/files/tests/test_endpoints.py
```

### Test Coverage

- **42 total tests** covering all functionality
- **View Tests**: Authentication, validation, rate limiting, pagination
- **Serializer Tests**: Field validation, file type detection, data representation
- **Integration Tests**: End-to-end API functionality
- **Rate Limiting Tests**: Proper rate limit enforcement
- **Error Handling Tests**: All error scenarios covered

## Usage Examples

### Django Views
```python
from apps.files.views import FileCreateView, FileListView

# Use in URL patterns
urlpatterns = [
    path('upload/', FileCreateView.as_view(), name='file-upload'),
    path('', FileListView.as_view(), name='file-list'),
]
```

### Serializers
```python
from apps.files.serializers import CreateFileSerializer, FileSerializer

# For file upload
create_serializer = CreateFileSerializer(data=request.data)
if create_serializer.is_valid():
    file_instance = create_serializer.save()

# For file listing
files = File.objects.all()
list_serializer = FileSerializer(files, many=True)
```

### Testing
```python
from apps.files.tests.constants import ALLOWED_FILE_EXTENSIONS, TEST_FILE_CONTENT

# Create test file
test_file = SimpleUploadedFile(
    "test.pdf", TEST_FILE_CONTENT, content_type="application/pdf"
)

# Test file upload
response = self.client.post(url, {"file": test_file}, format="multipart")
```

## Migration from Legacy Code

### Backward Compatibility
- Legacy imports still work via `views.py` and `serializers.py`
- Old URL patterns continue to function
- Existing tests remain functional

### Recommended Migration Path
1. Update imports to use new modular structure
2. Update URL patterns to use separate endpoints
3. Update tests to use new test structure
4. Remove legacy files after migration complete

### Breaking Changes
- URL structure changed from single endpoint to separate endpoints
- Response format uses `meta` object for pagination
- Rate limiting now properly enforced

## Configuration

### Settings
```python
# Rate limiting
RATE_LIMITER_ENABLED = True
RATE_LIMITER_DEFAULT_RATE = 5
RATE_LIMITER_DEFAULT_PERIOD = 60

# File upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Allowed File Extensions
To modify allowed file extensions, update the `CreateFileSerializer`:

```python
# In apps/files/serializers/create.py
allowed_extensions = [
    "pdf", "docx", "doc", "xls", "xlsx", "csv", "txt",
    "png", "jpg", "jpeg", "mp4", "mp3"
]
```

## Best Practices

### Development
- Use separate views for different HTTP methods
- Implement proper error handling with `@api_error_handler`
- Add rate limiting with `@dynamic_rate_limit`
- Write comprehensive tests for all functionality
- Follow Django naming conventions

### Security
- Always validate file extensions
- Implement rate limiting on upload endpoints
- Use authentication for all file operations
- Sanitize file names (UUID-based naming)
- Validate file content when necessary

### Performance
- Use pagination for file listings
- Implement caching for frequently accessed data
- Optimize database queries with select_related/prefetch_related
- Consider file size limits for uploads

## Contributing

When adding new functionality:

1. Create separate view files for each action
2. Create corresponding serializer files
3. Add comprehensive tests
4. Update this README
5. Maintain backward compatibility
6. Follow the established patterns

## Dependencies

- Django REST Framework
- django-ratelimit (for rate limiting)
- drf-spectacular (for API documentation)
- django-filter (for filtering)
- Pillow (for image handling)

## License

This module is part of the larger Django project and follows the same license terms. 