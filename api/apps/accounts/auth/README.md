# Authentication App

The `accounts/auth` app provides comprehensive authentication functionality for the platform, extending and customizing Django's built-in authentication system and integrating with Djoser and Simple JWT for token-based authentication.

## Features

- User registration and account creation
- Login and token-based authentication
- Password reset and management
- Social authentication (OAuth2)
- Email verification
- Token refresh and validation
- Multi-factor authentication support
- Rate limiting for authentication endpoints

## API Endpoints

All authentication endpoints are protected with rate limiting to prevent brute force attacks.

### Registration

- **URL**: `POST /api/auth/users/`
- **Rate Limit**: 5 requests per minute
- **Description**: Creates a new user account
- **Request Body**:
  - `email`: User's email (required)
  - `password`: User's password (required)
  - `re_password`: Password confirmation (required)
  - `fullname`: User's full name (required)
  - Other optional user fields

### Login (JWT Token)

- **URL**: `POST /api/auth/jwt/create/`
- **Rate Limit**: 10 requests per minute
- **Description**: Authenticates a user and returns JWT tokens
- **Request Body**:
  - `email`: User's email
  - `password`: User's password
- **Response**:
  - `access`: Short-lived JWT access token
  - `refresh`: Long-lived JWT refresh token

### Token Refresh

- **URL**: `POST /api/auth/jwt/refresh/`
- **Rate Limit**: 20 requests per minute
- **Description**: Refreshes an access token using a valid refresh token
- **Request Body**:
  - `refresh`: Valid refresh token
- **Response**:
  - `access`: New JWT access token

### Token Verify

- **URL**: `POST /api/auth/jwt/verify/`
- **Rate Limit**: 20 requests per minute
- **Description**: Verifies that a JWT token is valid
- **Request Body**:
  - `token`: JWT token to verify

### Password Reset

- **URL**: `POST /api/auth/users/reset_password/`
- **Rate Limit**: 5 requests per hour
- **Description**: Initiates password reset process
- **Request Body**:
  - `email`: User's email address

### Password Reset Confirmation

- **URL**: `POST /api/auth/users/reset_password_confirm/`
- **Rate Limit**: 5 requests per hour
- **Description**: Completes password reset using token
- **Request Body**:
  - `uid`: User ID encoded in base64
  - `token`: Password reset token
  - `new_password`: New password
  - `re_new_password`: New password confirmation

### User Activation

- **URL**: `POST /api/auth/users/activation/`
- **Rate Limit**: 5 requests per hour
- **Description**: Activates a user account
- **Request Body**:
  - `uid`: User ID encoded in base64
  - `token`: Activation token

### Social Authentication

- **URL**: `POST /api/auth/social/{provider}/`
- **Rate Limit**: 10 requests per minute
- **Description**: Authenticates using a social provider (Google, Facebook, etc.)
- **Request Body**:
  - `access_token`: Access token from social provider
  - `code`: Authorization code (alternative to access_token)

## Architecture

The auth app extends Djoser and Simple JWT functionality with customizations:

### Serializers

Located in `serializers/` directory:

- `user_create.py`: Extended serializer for user registration
- `token.py`: Custom token serializers
- `jwt.py`: JWT token customizations

### Views

Located in `views/` directory:

- `jwt.py`: Custom JWT token views
- `user.py`: User-related auth views
- `social.py`: Social authentication views

### Custom JWT Settings

Customized JWT settings include:

- Short-lived access tokens (5-15 minutes)
- Longer-lived refresh tokens (24 hours - 7 days)
- Custom token payload with user roles and permissions
- Blacklisting of used tokens

### Email Templates

Custom email templates for:

- Account activation
- Password reset
- Email verification

## Security Features

The auth app implements several security best practices:

1. **Rate Limiting**: All authentication endpoints have strict rate limits to prevent brute force attacks
2. **Password Validation**: Enforces password complexity requirements
3. **Token Blacklisting**: Used tokens can be blacklisted to prevent replay attacks
4. **Short-lived Tokens**: Access tokens expire quickly to reduce risk if compromised
5. **CSRF Protection**: For cookie-based authentication scenarios
6. **Secure Cookie Settings**: HttpOnly and Secure flags for production

## Social Authentication

The app supports OAuth2 authentication with various providers:

- Google
- Facebook
- Apple
- Other configurable providers

## Testing

Comprehensive test suite in `tests/` directory:

- Unit tests for serializers and views
- Integration tests for the authentication flow
- Security tests for rate limiting and token validation
- Mock tests for social authentication 