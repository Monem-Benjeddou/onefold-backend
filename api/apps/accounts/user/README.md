# User Management App

The `accounts/user` app provides core user management functionality for the platform. It handles user creation, updates, deletion, role management, and export capabilities.

## Features

- User CRUD operations (Create, Read, Update, Delete)
- User role management
- User export with extensive filtering options
- Rate limiting for all endpoints

## Models

### User

A custom User model that extends Django's `AbstractUser` with additional fields:

- `_id`: UUID primary key
- `fullname`: User's full name
- `phone_number`: User's phone number (optional)
- `location`: User's location (optional)
- `company_information`: User's company information (optional)
- `role`: User's role (user, admin, moderator, influencer, service, manufacturer, collector, issuer)
- `country`: Foreign key to Country model
- `avatar`: User profile image
- `job_title`: User's job title (optional)
- `profession_id`: User's profession ID (optional)

## API Endpoints

All endpoints are protected with appropriate permissions and rate limiting.

### List Users

- **URL**: `GET /api/accounts/user/`
- **Permissions**: IsAuthenticated, IsBusinessAdminOrNeoAdmin
- **Rate Limit**: 20 requests per minute
- **Description**: Retrieves a paginated list of users
- **Query Parameters**:
  - `search`: Search by username, email, fullname, or role
  - `role`: Filter by user role
  - `include_superusers`: Include superuser accounts (default: false)
  - `is_active`: Filter by active status

### Create User

- **URL**: `POST /api/accounts/user/create/`
- **Permissions**: IsAuthenticated, IsBusinessAdminOrNeoAdmin
- **Rate Limit**: 5 requests per minute
- **Description**: Creates a new user
- **Request Body**:
  - `email`: User's email (required)
  - `fullname`: User's full name (required)
  - `password`: User's password (optional)
  - `role`: User's role (optional, defaults to "user")
  - `avatar`: User's profile image (optional)
  - Other optional fields (phone_number, location, etc.)

### Update User

- **URL**: `PUT /api/accounts/user/<uuid:pk>/`
- **Permissions**: IsAuthenticated, IsBusinessAdminOrNeoAdmin
- **Rate Limit**: 10 requests per minute
- **Description**: Updates a user's information
- **Request Body**: Same fields as Create User

### Partial Update User

- **URL**: `PATCH /api/accounts/user/<uuid:pk>/partial/`
- **Permissions**: IsAuthenticated, IsBusinessAdminOrNeoAdmin
- **Rate Limit**: 15 requests per minute
- **Description**: Partially updates a user's information
- **Request Body**: Any subset of user fields

### Delete User

- **URL**: `DELETE /api/accounts/user/delete/<uuid:pk>/`
- **Permissions**: IsAuthenticated, IsBusinessAdminOrNeoAdmin
- **Rate Limit**: 5 requests per minute
- **Description**: Deletes a user

### Update User Role

- **URL**: `PATCH /api/accounts/user/<uuid:pk>/update-role/`
- **Permissions**: IsAuthenticated, IsBusinessAdminOrNeoAdmin
- **Rate Limit**: 10 requests per minute
- **Description**: Updates a user's role
- **Request Body**:
  - `role`: New role (user, admin, moderator, influencer, service, manufacturer, collector, issuer)

### Export Users

- **URL**: `GET /api/accounts/user/export/`
- **Permissions**: IsAuthenticated, IsBusinessAdminOrNeoAdmin
- **Rate Limit**: 5 requests per 5 minutes
- **Description**: Exports user data in CSV or JSON format
- **Query Parameters**:
  - `format`: Export format (csv or json, defaults to csv)
  - `search`: Search by username, email, fullname, or role
  - `role`: Filter by user role
  - `email`: Filter by email (contains)
  - `email_exact`: Filter by exact email match
  - `email_domain`: Filter by email domain
  - `username`: Filter by username (contains)
  - `is_active`: Filter by active status
  - `exclude_staff`: Exclude staff users
  - `inactive_only`: Include only inactive users
  - `never_logged_in`: Filter to users who have never logged in
  - `has_logged_in`: Filter to users who have logged in
  - `include_superusers`: Include superuser accounts

## Architecture

The app follows a clean architecture with separation of concerns:

### Serializers

Located in `serializers/` directory:

- `user.py`: Base user serializer with common fields and methods
- `create_user.py`: Serializer for user creation with specific validation
- `update_user.py`: Serializer for user updates
- `export_user.py`: Serializer for user exports with additional fields

### Views

Located in `views/` directory, one file per action:

- `list_users.py`: View for listing users with filtering
- `create_user.py`: View for creating users
- `update_user.py`: View for full updates
- `partial_update_user.py`: View for partial updates
- `delete_user.py`: View for deleting users
- `update_role.py`: View for role updates
- `export_users.py`: View for exporting users

### Permissions

Custom permission classes in `permissions.py`:
- `IsBusinessAdminOrNeoAdmin`: Restricts access to users with admin roles

### Rate Limiting

All endpoints use the `dynamic_rate_limit` decorator with specific limits per operation:
- Higher limits for read operations (listing: 20/min)
- Medium limits for updates (updates: 10-15/min)
- Lower limits for sensitive operations (creation/deletion: 5/min)
- Very low limits for resource-intensive operations (exports: 5/5min)

## Error Handling

All views use the `api_error_handler` decorator for consistent error responses. Custom error handling provides:

1. Proper 404 responses for non-existent users
2. Field validation errors with descriptive messages
3. Rate limit exceeded messages
4. Internal server error handling with logging

## Testing

Comprehensive test suite located in `tests/`:

- Unit tests for models, views, and serializers
- Integration tests for API endpoints
- Rate limiting tests
- Export functionality tests with various filter combinations 