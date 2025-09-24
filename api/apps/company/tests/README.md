

This directory contains comprehensive tests for the company app, covering all models, serializers, views, and permissions.



```
tests/
├── __init__.py                 
├── conftest.py                 
├── test_models.py              
├── test_serializers.py         
├── test_views.py               
├── test_permissions.py         
├── run_tests.py                
└── README.md                   # This file
```

## Test Coverage

### Models (`test_models.py`)
- **StartupProfile**: Creation, validation, string representation, properties, file uploads
- **StartupServiceProduct**: Creation, validation, relationships, defaults
- **DevelopmentStage**: Creation, validation, ordering
- **StartupDevelopmentStage**: Creation, validation, relationships
- **TargetedMarket**: Creation, validation, relationships
- **CompanyMember**: Creation, validation, member types, relationships

### Serializers (`test_serializers.py`)
- **StartupProfileSerializer**: Serialization, deserialization, validation, read-only fields
- **StartupProfileCreateSerializer**: Creation with nested objects
- **StartupProfileUpdateSerializer**: Partial updates
- **StartupServiceProductSerializer**: CRUD operations, validation
- **DevelopmentStageSerializer**: CRUD operations, validation
- **StartupDevelopmentStageSerializer**: CRUD operations, read-only fields
- **TargetedMarketSerializer**: CRUD operations, validation
- **CompanyMemberSerializer**: CRUD operations, member type validation

### Views (`test_views.py`)
- **StartupProfileViewSet**: List, retrieve, create, update, delete operations
- **StartupServiceProductViewSet**: CRUD operations, ownership filtering
- **DevelopmentStageViewSet**: CRUD operations (admin only)
- **StartupDevelopmentStageViewSet**: CRUD operations, ownership filtering
- **TargetedMarketViewSet**: CRUD operations, ownership filtering
- **CompanyMemberViewSet**: CRUD operations, membership management

### Permissions (`test_permissions.py`)
- **StartupAccessPermission**: Role-based access control
- **Ownership Permissions**: Founder access to own startups only
- **Admin Permissions**: Full access for admin users
- **Reviewer Permissions**: Read-only access for reviewers
- **Member Permissions**: Company member access controls

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
python api/apps/company/tests/run_tests.py

# Run specific test types
python api/apps/company/tests/run_tests.py --models
python api/apps/company/tests/run_tests.py --serializers
python api/apps/company/tests/run_tests.py --views
python api/apps/company/tests/run_tests.py --permissions

# Run with verbose output
python api/apps/company/tests/run_tests.py --verbose

# Run with coverage report
python api/apps/company/tests/run_tests.py --coverage
```

### Using pytest directly

```bash
# Run all company app tests
pytest api/apps/company/tests/

# Run specific test files
pytest api/apps/company/tests/test_models.py
pytest api/apps/company/tests/test_serializers.py
pytest api/apps/company/tests/test_views.py
pytest api/apps/company/tests/test_permissions.py

# Run with verbose output
pytest api/apps/company/tests/ -v

# Run with coverage
pytest api/apps/company/tests/ --cov=apps.company --cov-report=html
```

### Using Django's test runner

```bash
# Run all company app tests
python api/manage.py test apps.company.tests

# Run specific test classes
python api/manage.py test apps.company.tests.test_models.TestStartupProfile
python api/manage.py test apps.company.tests.test_views.TestStartupProfileViewSet
```

## Test Fixtures

The `conftest.py` file provides comprehensive fixtures for testing:

- **User fixtures**: `user`, `admin_user`, `reviewer_user`
- **Startup fixtures**: `startup_profile`, `another_startup_profile`
- **Service fixtures**: `startup_service_product`
- **Development stage fixtures**: `development_stage`, `startup_development_stage`
- **Market fixtures**: `targeted_market`
- **Member fixtures**: `company_member`
- **File fixtures**: `test_image`, `test_pitch_deck`

## Test Data

Tests use realistic test data that covers various scenarios:

- Different user roles (founder, admin, reviewer, employee)
- Various startup industries and locations
- Different development stages and market segments
- Multiple service/product types
- Various company member roles

## Assertions and Validations

Tests include comprehensive assertions for:

- HTTP status codes
- Response data structure and content
- Database state changes
- Permission enforcement
- Validation error handling
- File upload functionality
- Relationship integrity

## Best Practices

The tests follow Django and pytest best practices:

- **Isolation**: Each test is independent and doesn't affect others
- **Fixtures**: Reusable test data through pytest fixtures
- **Descriptive names**: Clear test method names that describe what is being tested
- **Comprehensive coverage**: Tests cover happy paths, edge cases, and error conditions
- **Realistic data**: Test data reflects real-world usage patterns
- **Performance**: Tests are optimized for fast execution

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

- No external dependencies
- Deterministic results
- Fast execution
- Clear failure reporting
- Coverage reporting support

## Debugging Tests

To debug failing tests:

1. Run with verbose output: `pytest -v`
2. Use `--pdb` to drop into debugger on failures
3. Use `--tb=long` for detailed tracebacks
4. Run specific test methods: `pytest::test_method_name`

## Adding New Tests

When adding new functionality to the company app:

1. Add model tests for new models or model changes
2. Add serializer tests for new serializers or validation changes
3. Add view tests for new endpoints or view logic changes
4. Add permission tests for new access control requirements
5. Update fixtures if new test data is needed
6. Ensure all tests pass before committing changes

