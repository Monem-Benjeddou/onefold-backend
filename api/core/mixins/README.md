# Core Mixins

This directory contains reusable mixins for Django REST Framework views that provide standardized functionality across the Kolct API.

## ExportMixin

The `ExportMixin` provides standardized export functionality for DRF views with comprehensive security features and performance optimizations.

### Features

- **Multiple Formats**: Support for CSV and JSON export formats
- **Field Selection**: Allow users to specify which fields to include via query parameters
- **ID Filtering**: Filter exports by specific record IDs
- **Custom Filenames**: Support for custom export filenames
- **Streaming Responses**: Automatic streaming for large datasets to prevent memory issues
- **Security Features**:
  - CSV injection prevention (sanitizes dangerous characters)
  - Filename sanitization to prevent path traversal attacks
  - Comprehensive audit logging for security monitoring
  - Rate limiting to prevent abuse
- **Performance Optimizations**:
  - Chunked processing for large datasets
  - Configurable chunk sizes and export limits
  - Memory-efficient streaming responses
- **Error Handling**: Robust validation and error handling
- **DRF Spectacular Integration**: Automatic API documentation generation

### Usage

#### Basic Usage with APIView

```python
from rest_framework.views import APIView
from core.mixins.export import ExportMixin

class MyExportView(ExportMixin, APIView):
    export_fields = ['id', 'name', 'email', 'created_at']
    export_filename_prefix = 'users'
    
    def get_queryset(self):
        return User.objects.all()
    
    def get_serializer_class(self):
        return UserSerializer
    
    def get(self, request):
        return self.export(request)
```

#### Usage with ViewSets

```python
from rest_framework import viewsets
from core.mixins.export import ModelExportMixin

class UserViewSet(ModelExportMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    export_fields = ['id', 'username', 'email', 'role']
    
    # Export action is automatically available at /users/export/
```

### Configuration Options

- `export_fields`: List of fields to include in exports (empty = all serializer fields)
- `export_filename_prefix`: Prefix for generated filenames
- `export_chunk_size`: Number of records to process in each chunk (default: 1000)
- `export_max_size`: Maximum number of records allowed in a single export (default: 50000)

### API Parameters

The export endpoint accepts the following query parameters:

- `format`: Export format (`csv` or `json`, default: `csv`)
- `fields`: Comma-separated list of fields to include
- `ids`: Comma-separated list of record IDs to export
- `filename`: Custom filename for the export

### Security Features

#### CSV Injection Prevention

The mixin automatically sanitizes CSV fields to prevent formula injection attacks:

```python
# Dangerous input: =SUM(A1:A10)
# Sanitized output: '=SUM(A1:A10)
```

#### Filename Sanitization

Filenames are sanitized to prevent path traversal and injection attacks:

```python
# Dangerous input: ../../../etc/passwd
# Sanitized output: ______etc_passwd.csv
```

#### Audit Logging

All export attempts are logged with comprehensive details:

```python
audit_logger.warning("DATA_EXPORT_ATTEMPT", extra={
    "user_id": user_id,
    "export_format": format_type,
    "record_count": count,
    "exported_fields": fields,
    "ip_address": ip,
    # ... additional context
})
```

#### Rate Limiting

Built-in rate limiting prevents abuse:

```python
@dynamic_rate_limit(default_rate=5, default_period=300)  # 5 exports per 5 minutes
```

### Performance Features

#### Streaming Responses

Large datasets are automatically streamed to prevent memory issues:

```python
# Automatically uses StreamingHttpResponse for large datasets
if queryset.count() > self.export_chunk_size:
    response = StreamingHttpResponse(generator(), content_type='text/csv')
```

#### Chunked Processing

Data is processed in configurable chunks:

```python
for offset in range(0, total_count, self.export_chunk_size):
    chunk = queryset[offset:offset + self.export_chunk_size]
    # Process chunk
```

### Error Handling

Comprehensive validation and error responses:

- Empty querysets return 400 with appropriate message
- Oversized exports return 400 with size limits
- Invalid formats return 400 with supported formats
- Invalid field names are filtered out automatically

### Integration with Existing Code

The mixin is designed to be compatible with existing export patterns. See `/api/core/examples/export_integration_example.py` for detailed migration examples.

#### Migration from Existing Export Views

1. **Add the mixin**: Inherit from `ExportMixin` or `ModelExportMixin`
2. **Configure fields**: Set `export_fields` class attribute
3. **Move queryset logic**: Move filtering logic to `get_export_queryset()`
4. **Replace export method**: Call `self.export()` instead of custom logic

### Testing

Comprehensive test suite available at `/api/core/tests/test_export_mixin.py` covering:

- Utility function testing
- Security feature validation
- Performance optimization verification
- Error handling scenarios
- Integration testing

### Dependencies

- Django REST Framework
- drf-spectacular (for API documentation)
- Core decorators and rate limiting

### Best Practices

1. **Always specify export_fields** to control what data is exported
2. **Set appropriate export_max_size** based on your data and performance requirements
3. **Override get_export_queryset()** for custom filtering logic
4. **Use ModelExportMixin** for simple model-based exports
5. **Monitor audit logs** for security and usage patterns
6. **Test with large datasets** to ensure performance is acceptable

### Examples

See `/api/core/examples/export_integration_example.py` for comprehensive examples including:

- Migrating existing export views
- ViewSet integration
- Custom filtering
- Admin-specific exports
- Error handling patterns