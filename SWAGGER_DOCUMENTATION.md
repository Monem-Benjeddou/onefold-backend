# Swagger API Documentation

## Overview

The Startup Founder Platform API now includes comprehensive Swagger/OpenAPI documentation for all CRUD operations. The documentation is automatically generated using DRF Spectacular and provides interactive API exploration capabilities.

## Accessing the Documentation

### Swagger UI (Interactive)
- **URL**: `http://localhost:8000/api/docs/`
- **Description**: Interactive API documentation with "Try it out" functionality
- **Features**: 
  - Test API endpoints directly from the browser
  - View request/response examples
  - Authentication support
  - Filter and search capabilities

### ReDoc (Alternative UI)
- **URL**: `http://localhost:8000/api/redoc/`
- **Description**: Clean, responsive API documentation
- **Features**: 
  - Better for reading and understanding API structure
  - Mobile-friendly interface
  - Search functionality

### OpenAPI Schema
- **JSON**: `http://localhost:8000/api/schema/`
- **YAML**: `http://localhost:8000/api/schema.yaml`
- **Description**: Raw OpenAPI schema for integration with other tools

## API Organization

The API is organized into the following main sections:

### 1. **Authentication** 🔐
- User registration and login
- JWT token management
- Password reset functionality

### 2. **Founders** 👤
- **Founder Profiles**: Complete founder information with social links, bio, avatar
- **Education**: Education history and qualifications
- **Previous Companies**: Work experience and previous startups

### 3. **Companies** 🏢
- **Startup Profiles**: Company information, social links, pitch decks
- **Development Stages**: Admin-configurable startup stages (Pre-Seed, Seed, Series A, etc.)
- **Company Members**: Team members and their roles
- **Targeted Markets**: Market analysis (Local, GCC, Global)

### 4. **Stakeholders** 🤝
- **Stakeholders**: Investors, advisors, partners, suppliers
- **Investors**: Detailed investor information with equity and investment data

### 5. **Competitors** 🏆
- **Competitors**: Competitor analysis by market scope (Local, GCC, Global)
- Threat level assessment and market share tracking

### 6. **Revenue** 💰
- **Revenue Models**: Admin-configurable revenue types (Subscription, Freemium, etc.)
- **Revenue Streams**: Detailed financial tracking and projections

### 7. **Funding** 💸
- **Funding Targets**: Fundraising goals and valuations
- **Raised Funds**: Historical funding rounds and investor information

## Key Features

### 🔍 **Advanced Filtering**
- Filter by multiple criteria (role, location, industry, etc.)
- Search across text fields
- Order by various fields

### 🏷️ **Tagged Organization**
- Endpoints grouped by functionality
- Easy navigation between related operations
- Consistent naming conventions

### 📝 **Comprehensive Documentation**
- Detailed descriptions for each endpoint
- Request/response examples
- Parameter descriptions
- Error response documentation

### 🔐 **Authentication Support**
- JWT token authentication
- Role-based permissions (User, Staff, Admin)
- Secure endpoint access

### 🎯 **Custom Actions**
- Specialized endpoints for common operations
- Bulk operations support
- Status management (verify, activate, etc.)

## Usage Examples

### 1. **Creating a Founder Profile**
```bash
POST /api/v1/founders/profiles/
{
  "full_name": "John Doe",
  "email_address": "john@example.com",
  "role": "ceo",
  "location": "Dubai, UAE",
  "bio": "Serial entrepreneur with 10+ years experience",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "education_history": [
    {
      "institution_name": "MIT",
      "degree": "Master of Science",
      "field_of_study": "Computer Science"
    }
  ]
}
```

### 2. **Creating a Startup Profile**
```bash
POST /api/v1/companies/startups/
{
  "startup_name": "TechCorp",
  "startup_industry": "Technology",
  "website_link": "https://techcorp.com",
  "location": "Dubai, UAE",
  "founded_year": 2023,
  "bio": "Revolutionary tech startup",
  "targeted_markets": [
    {
      "market_type": "gcc",
      "market_name": "GCC Technology Market",
      "market_size": 1000000000,
      "is_primary": true
    }
  ]
}
```

### 3. **Adding a Stakeholder**
```bash
POST /api/v1/stakeholders/stakeholders/
{
  "startup": "startup_uuid",
  "full_name": "Jane Smith",
  "stakeholder_type": "investor",
  "role_title": "Lead Investor",
  "influence_level": "high",
  "stake_interest_level": "high",
  "investment_amount": 500000
}
```

## Authentication

### Getting an Access Token
```bash
POST /api/v1/auth/login/
{
  "email": "user@example.com",
  "password": "your_password"
}
```

### Using the Token
Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## Admin Operations

### Development Stages
- **List**: `GET /api/v1/companies/development-stages/`
- **Create**: `POST /api/v1/companies/development-stages/` (Admin only)
- **Activate**: `POST /api/v1/companies/development-stages/{id}/activate/` (Admin only)

### Revenue Models
- **List**: `GET /api/v1/revenue/models/`
- **Create**: `POST /api/v1/revenue/models/` (Admin only)
- **Assign to Startup**: `POST /api/v1/revenue/models/{id}/assign_to_startup/`

## Custom Actions

### Founder Profiles
- `GET /api/v1/founders/profiles/my_profile/` - Get current user's profile
- `POST /api/v1/founders/profiles/{id}/verify/` - Verify profile (Staff only)

### Startup Profiles
- `GET /api/v1/companies/startups/my_startups/` - Get user's startups
- `GET /api/v1/companies/startups/verified_startups/` - Get verified startups
- `GET /api/v1/companies/startups/by_industry/?industry=Technology` - Filter by industry

### Stakeholders
- `GET /api/v1/stakeholders/stakeholders/investors/` - Get investor stakeholders
- `GET /api/v1/stakeholders/stakeholders/advisors/` - Get advisor stakeholders
- `GET /api/v1/stakeholders/stakeholders/high_influence/` - Get high influence stakeholders

### Competitors
- `GET /api/v1/competitors/competitors/local_competitors/` - Get local competitors
- `GET /api/v1/competitors/competitors/gcc_competitors/` - Get GCC competitors
- `GET /api/v1/competitors/competitors/global_competitors/` - Get global competitors
- `GET /api/v1/competitors/competitors/high_threat/` - Get high threat competitors

### Revenue
- `GET /api/v1/revenue/models/active_models/` - Get active revenue models
- `GET /api/v1/revenue/streams/recurring_streams/` - Get recurring revenue streams
- `GET /api/v1/revenue/streams/top_revenue_streams/` - Get top revenue streams

### Funding
- `GET /api/v1/funding/targets/active_targets/` - Get active funding targets
- `GET /api/v1/funding/targets/seed_stage/` - Get seed stage targets
- `GET /api/v1/funding/raised-funds/announced_funds/` - Get announced funding
- `GET /api/v1/funding/raised-funds/recent_funding/` - Get recent funding rounds

## Error Handling

The API provides comprehensive error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error message",
  "field_name": ["Specific field error"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "Permission denied."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

## Best Practices

### 1. **Use Filtering**
- Leverage the built-in filtering capabilities
- Use search parameters for text fields
- Apply ordering for consistent results

### 2. **Handle Pagination**
- All list endpoints support pagination
- Use `page` and `page_size` parameters
- Check response headers for pagination info

### 3. **Optimize Queries**
- Use specific endpoints for common operations
- Leverage custom actions for specialized queries
- Use filtering to reduce data transfer

### 4. **Error Handling**
- Always check response status codes
- Handle validation errors gracefully
- Implement retry logic for transient errors

## Development

### Adding New Endpoints
1. Create the viewset with proper OpenAPI decorators
2. Add appropriate tags and descriptions
3. Include request/response schemas
4. Document custom actions
5. Test in Swagger UI

### Updating Documentation
- Documentation is automatically generated from code
- Update docstrings and decorators for changes
- Test documentation in Swagger UI
- Verify all endpoints are properly documented

## Support

For API support and questions:
- Check the Swagger UI for interactive documentation
- Review the ReDoc for detailed API structure
- Examine the OpenAPI schema for integration details
- Test endpoints directly in Swagger UI

The Swagger documentation provides a complete, interactive guide to all API endpoints, making it easy to understand, test, and integrate with the Startup Founder Platform API.
