# Startup Founder Platform API Documentation

This document provides comprehensive documentation for the Startup Founder Platform API, which includes CRUD operations for managing founder profiles, startup companies, stakeholders, competitors, revenue models, and funding information.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Usage Examples](#usage-examples)
6. [Seeding Data](#seeding-data)

## Overview

The Startup Founder Platform API is built with Django REST Framework and provides a comprehensive set of endpoints for managing startup ecosystem data. The API is organized into the following main modules:

- **Founder Management**: Founder profiles, education, and previous work experience
- **Company Management**: Startup profiles, development stages, team members, and target markets
- **Stakeholder Management**: Investors, advisors, partners, and other stakeholders
- **Competitor Analysis**: Local, GCC, and global competitors
- **Revenue Management**: Revenue models and revenue streams
- **Funding Management**: Funding targets and raised funds

## Authentication

All API endpoints require authentication. Use the authentication endpoints to obtain access tokens:

```
POST /api/v1/auth/login/
POST /api/v1/auth/register/
```

Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## API Endpoints

### Founder Management

#### Founder Profiles
- `GET /api/v1/founders/profiles/` - List all founder profiles
- `POST /api/v1/founders/profiles/` - Create a new founder profile
- `GET /api/v1/founders/profiles/{id}/` - Get specific founder profile
- `PUT /api/v1/founders/profiles/{id}/` - Update founder profile
- `DELETE /api/v1/founders/profiles/{id}/` - Delete founder profile
- `GET /api/v1/founders/profiles/my_profile/` - Get current user's profile
- `POST /api/v1/founders/profiles/{id}/verify/` - Verify founder profile (staff only)

#### Education Records
- `GET /api/v1/founders/education/` - List education records
- `POST /api/v1/founders/education/` - Create education record
- `GET /api/v1/founders/education/my_education/` - Get current user's education
- `GET /api/v1/founders/education/current_education/` - Get current education records

#### Previous Companies
- `GET /api/v1/founders/previous-companies/` - List previous companies
- `POST /api/v1/founders/previous-companies/` - Create previous company record
- `GET /api/v1/founders/previous-companies/my_companies/` - Get current user's companies

### Company Management

#### Startup Profiles
- `GET /api/v1/companies/startups/` - List all startup profiles
- `POST /api/v1/companies/startups/` - Create new startup profile
- `GET /api/v1/companies/startups/{id}/` - Get specific startup profile
- `PUT /api/v1/companies/startups/{id}/` - Update startup profile
- `DELETE /api/v1/companies/startups/{id}/` - Delete startup profile
- `GET /api/v1/companies/startups/my_startups/` - Get current user's startups
- `GET /api/v1/companies/startups/verified_startups/` - Get verified startups
- `POST /api/v1/companies/startups/{id}/verify/` - Verify startup (staff only)

#### Development Stages
- `GET /api/v1/companies/development-stages/` - List development stages
- `POST /api/v1/companies/development-stages/` - Create development stage (admin only)
- `GET /api/v1/companies/development-stages/active_stages/` - Get active stages
- `POST /api/v1/companies/development-stages/{id}/activate/` - Activate stage (admin only)

#### Company Members
- `GET /api/v1/companies/members/` - List company members
- `POST /api/v1/companies/members/` - Add company member
- `GET /api/v1/companies/members/my_memberships/` - Get current user's memberships
- `GET /api/v1/companies/members/current_members/` - Get current members

#### Targeted Markets
- `GET /api/v1/companies/targeted-markets/` - List targeted markets
- `POST /api/v1/companies/targeted-markets/` - Create targeted market
- `GET /api/v1/companies/targeted-markets/local_markets/` - Get local markets
- `GET /api/v1/companies/targeted-markets/gcc_markets/` - Get GCC markets
- `GET /api/v1/companies/targeted-markets/global_markets/` - Get global markets

### Stakeholder Management

#### Stakeholders
- `GET /api/v1/stakeholders/stakeholders/` - List stakeholders
- `POST /api/v1/stakeholders/stakeholders/` - Create stakeholder
- `GET /api/v1/stakeholders/stakeholders/investors/` - Get investor stakeholders
- `GET /api/v1/stakeholders/stakeholders/advisors/` - Get advisor stakeholders
- `GET /api/v1/stakeholders/stakeholders/partners/` - Get partner stakeholders

#### Investors
- `GET /api/v1/stakeholders/investors/` - List investors
- `POST /api/v1/stakeholders/investors/` - Create investor record
- `GET /api/v1/stakeholders/investors/lead_investors/` - Get lead investors
- `GET /api/v1/stakeholders/investors/board_members/` - Get board members
- `GET /api/v1/stakeholders/investors/angel_investors/` - Get angel investors

### Competitor Management

#### Competitors
- `GET /api/v1/competitors/competitors/` - List competitors
- `POST /api/v1/competitors/competitors/` - Create competitor
- `GET /api/v1/competitors/competitors/local_competitors/` - Get local competitors
- `GET /api/v1/competitors/competitors/gcc_competitors/` - Get GCC competitors
- `GET /api/v1/competitors/competitors/global_competitors/` - Get global competitors
- `GET /api/v1/competitors/competitors/high_threat/` - Get high threat competitors

### Revenue Management

#### Revenue Models
- `GET /api/v1/revenue/models/` - List revenue models
- `POST /api/v1/revenue/models/` - Create revenue model (admin only)
- `GET /api/v1/revenue/models/active_models/` - Get active revenue models
- `POST /api/v1/revenue/models/{id}/assign_to_startup/` - Assign model to startup

#### Revenue Streams
- `GET /api/v1/revenue/streams/` - List revenue streams
- `POST /api/v1/revenue/streams/` - Create revenue stream
- `GET /api/v1/revenue/streams/recurring_streams/` - Get recurring streams
- `GET /api/v1/revenue/streams/top_revenue_streams/` - Get top revenue streams

### Funding Management

#### Funding Targets
- `GET /api/v1/funding/targets/` - List funding targets
- `POST /api/v1/funding/targets/` - Create funding target
- `GET /api/v1/funding/targets/active_targets/` - Get active targets
- `GET /api/v1/funding/targets/seed_stage/` - Get seed stage targets

#### Raised Funds
- `GET /api/v1/funding/raised-funds/` - List raised funds
- `POST /api/v1/funding/raised-funds/` - Create raised fund record
- `GET /api/v1/funding/raised-funds/announced_funds/` - Get announced funds
- `GET /api/v1/funding/raised-funds/recent_funding/` - Get recent funding
- `POST /api/v1/funding/raised-funds/{id}/announce/` - Announce funding round

## Data Models

### Founder Profile
```json
{
  "id": "uuid",
  "full_name": "string",
  "email_address": "email",
  "role": "ceo|cto|cmo|cfo|coo|cpo|cso|founder|co_founder|other",
  "location": "string",
  "birthdate": "date",
  "linkedin_url": "url",
  "twitter_url": "url",
  "facebook_url": "url",
  "instagram_url": "url",
  "github_url": "url",
  "personal_website": "url",
  "bio": "text",
  "avatar": "image",
  "background_image": "image",
  "is_verified": "boolean",
  "is_public": "boolean",
  "education_history": [...],
  "previous_companies": [...]
}
```

### Startup Profile
```json
{
  "id": "uuid",
  "startup_name": "string",
  "startup_industry": "string",
  "website_link": "url",
  "location": "string",
  "founded_year": "integer",
  "bio": "text",
  "services_and_products": "text",
  "linkedin_url": "url",
  "twitter_url": "url",
  "facebook_url": "url",
  "instagram_url": "url",
  "youtube_url": "url",
  "logo": "image",
  "pitch_deck_link": "url",
  "pitch_deck_file": "file",
  "is_verified": "boolean",
  "is_public": "boolean",
  "is_active": "boolean",
  "primary_founder": "user_id",
  "members": [...],
  "targeted_markets": [...],
  "development_stage": {...}
}
```

### Development Stage
```json
{
  "id": "uuid",
  "name": "string",
  "description": "text",
  "order": "integer",
  "is_active": "boolean"
}
```

### Stakeholder
```json
{
  "id": "uuid",
  "startup": "startup_id",
  "full_name": "string",
  "stakeholder_type": "investor|advisor|partner|supplier|member|customer|vendor|other",
  "role_title": "string",
  "influence_level": "high|medium|low",
  "stake_interest_level": "high|medium|low",
  "ownership_percentage": "decimal",
  "investment_amount": "decimal",
  "contact_email": "email",
  "contact_phone": "string",
  "company_name": "string",
  "description": "text",
  "is_active": "boolean"
}
```

### Competitor
```json
{
  "id": "uuid",
  "startup": "startup_id",
  "competitor_type": "local|gcc|global",
  "competitor_name": "string",
  "competitor_url": "url",
  "description": "text",
  "market_share": "decimal",
  "funding_raised": "decimal",
  "founded_year": "integer",
  "employee_count": "integer",
  "location": "string",
  "strengths": "text",
  "weaknesses": "text",
  "threat_level": "high|medium|low",
  "is_active": "boolean"
}
```

### Revenue Model
```json
{
  "id": "uuid",
  "name": "string",
  "description": "text",
  "order": "integer",
  "is_active": "boolean"
}
```

### Revenue Stream
```json
{
  "id": "uuid",
  "startup": "startup_id",
  "name": "string",
  "description": "text",
  "monthly_revenue": "decimal",
  "annual_revenue": "decimal",
  "revenue_percentage": "decimal",
  "is_recurring": "boolean",
  "is_active": "boolean",
  "start_date": "date",
  "end_date": "date"
}
```

### Funding Target
```json
{
  "id": "uuid",
  "startup": "startup_id",
  "target_amount": "decimal",
  "pre_money_valuation": "decimal",
  "post_money_valuation": "decimal",
  "funding_round": "pre_seed|seed|series_a|series_b|series_c|series_d|mezzanine|ipo",
  "use_of_funds": "text",
  "timeline": "string",
  "is_active": "boolean"
}
```

### Raised Fund
```json
{
  "id": "uuid",
  "startup": "startup_id",
  "amount_raised": "decimal",
  "funding_round": "pre_seed|seed|series_a|series_b|series_c|series_d|mezzanine|ipo|debt|grant|other",
  "funding_date": "date",
  "lead_investor": "string",
  "participating_investors": "text",
  "pre_money_valuation": "decimal",
  "post_money_valuation": "decimal",
  "equity_offered": "decimal",
  "use_of_funds": "text",
  "is_announced": "boolean",
  "announcement_date": "date",
  "description": "text"
}
```

## Usage Examples

### Creating a Founder Profile

```bash
curl -X POST http://localhost:8000/api/v1/founders/profiles/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
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
        "field_of_study": "Computer Science",
        "start_date": "2010-09-01",
        "end_date": "2012-06-01"
      }
    ]
  }'
```

### Creating a Startup Profile

```bash
curl -X POST http://localhost:8000/api/v1/companies/startups/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "startup_name": "TechCorp",
    "startup_industry": "Technology",
    "website_link": "https://techcorp.com",
    "location": "Dubai, UAE",
    "founded_year": 2023,
    "bio": "Revolutionary tech startup",
    "services_and_products": "AI-powered solutions",
    "targeted_markets": [
      {
        "market_type": "gcc",
        "market_name": "GCC Technology Market",
        "market_size": 1000000000,
        "is_primary": true
      }
    ]
  }'
```

### Adding a Stakeholder

```bash
curl -X POST http://localhost:8000/api/v1/stakeholders/stakeholders/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "startup": "startup_uuid",
    "full_name": "Jane Smith",
    "stakeholder_type": "investor",
    "role_title": "Lead Investor",
    "influence_level": "high",
    "stake_interest_level": "high",
    "investment_amount": 500000,
    "contact_email": "jane@investor.com"
  }'
```

## Seeding Data

To populate the database with initial data, run the following management commands:

```bash
# Seed all data
python manage.py seed_all_data

# Or seed individually
python manage.py seed_development_stages
python manage.py seed_revenue_models
```

## Features

### Key Features Implemented:

1. **Complete CRUD Operations**: All models have full Create, Read, Update, Delete operations
2. **Nested Relationships**: Support for nested data creation and updates
3. **Filtering and Search**: Advanced filtering and search capabilities
4. **Custom Actions**: Specialized endpoints for common operations
5. **Permission Control**: Role-based access control
6. **Data Validation**: Comprehensive input validation
7. **Admin Integration**: Admin-configurable development stages and revenue models
8. **File Uploads**: Support for images and documents
9. **Social Media Integration**: Multiple social media platform support
10. **Financial Calculations**: Automatic calculation of valuations and percentages

### Development Stages (Admin Configurable):
- Pre-Seed/Ideation
- Seed
- Series A
- Series B
- Series C
- Series D
- Mezzanine (Pre-IPO)

### Revenue Models (Admin Configurable):
- Subscription (SaaS / Recurring)
- Freemium
- Advertising
- Commission / Transaction Fee
- Marketplace Fee (Take Rate)
- One-Time Purchase

### Market Types:
- Local
- GCC (Gulf Cooperation Council)
- Global

### Stakeholder Types:
- Investor
- Advisor
- Partner
- Supplier
- Member
- Customer
- Vendor
- Other

This API provides a comprehensive foundation for building startup ecosystem management applications with full CRUD operations and advanced features.
