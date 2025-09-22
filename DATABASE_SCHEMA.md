# Founder Account System - Database Schema

## Overview
This document outlines the normalized database design for the founder account system with separate Django apps for different components.

## Apps Structure

### 1. Accounts App (`apps.accounts`)
- **Base User Model**: `accounts_auth.User` (existing)
- **Founder App**: `apps.accounts.founder`

#### Founder Models:
- **FounderProfile**: Extended profile for founder users
  - One-to-One with User
  - Contains: full_name, email, role, location, birthdate, social links, bio, avatar, background_image
- **Education**: Education history for founders
  - Foreign Key to FounderProfile
  - Contains: institution_name, degree, field_of_study, dates, GPA, description
- **PreviousCompany**: Previous companies/startups worked at
  - Foreign Key to FounderProfile
  - Contains: company_name, position, dates, company_type, industry, size

### 2. Company App (`apps.company`)

#### Company Models:
- **StartupProfile**: Main startup/company profile
  - Contains: startup_name, industry, website, location, founded_year, bio, social links, logo, pitch_deck
  - Foreign Key to User (primary_founder)
- **DevelopmentStage**: Configurable development stages
  - Admin-configurable stages (Pre-Seed, Seed, Series A, etc.)
- **StartupDevelopmentStage**: Links startups to their current stage
  - One-to-One with StartupProfile
- **TargetedMarket**: Target markets with size and share
  - Foreign Key to StartupProfile
  - Contains: market_type (Local/GCC/Global), market_name, market_size, market_share
- **CompanyMember**: Team members of startups
  - Foreign Key to StartupProfile and User
  - Contains: member_type, position, dates, equity_percentage

### 3. Stakeholder App (`apps.stakeholder`)

#### Stakeholder Models:
- **Stakeholder**: General stakeholders (investors, advisors, partners, suppliers)
  - Foreign Key to StartupProfile
  - Contains: full_name, type, role, influence_level, stake_level, ownership_percentage, investment_amount
- **Investor**: Detailed investor information
  - Foreign Key to StartupProfile
  - Contains: person_company_name, address, contact, equity, investment_type, amount, dates

### 4. Competitor App (`apps.competitor`)

#### Competitor Models:
- **Competitor**: Competitors categorized by market scope
  - Foreign Key to StartupProfile
  - Contains: competitor_type (Local/GCC/Global), competitor_name, URL, description, market_share, funding_raised

### 5. Revenue App (`apps.revenue`)

#### Revenue Models:
- **RevenueModel**: Configurable revenue model types
  - Admin-configurable models (Subscription, Freemium, Advertising, etc.)
- **StartupRevenueModel**: Links startups to revenue models (many-to-many)
  - Foreign Key to StartupProfile and RevenueModel
  - Contains: is_primary, percentage, description
- **RevenueStream**: Detailed revenue streams
  - Foreign Key to StartupProfile
  - Contains: name, description, monthly/annual revenue, percentage, is_recurring

### 6. Funding App (`apps.funding`)

#### Funding Models:
- **FundingTarget**: Funding targets and valuations
  - One-to-One with StartupProfile
  - Contains: target_amount, pre_money_valuation, post_money_valuation, funding_round, use_of_funds
- **RaisedFund**: Records of funds raised
  - Foreign Key to StartupProfile
  - Contains: amount_raised, funding_round, dates, lead_investor, valuations, equity_offered

## Key Relationships

1. **User → FounderProfile**: One-to-One
2. **FounderProfile → Education**: One-to-Many
3. **FounderProfile → PreviousCompany**: One-to-Many
4. **User → StartupProfile**: One-to-Many (as primary_founder)
5. **StartupProfile → DevelopmentStage**: Many-to-One (via StartupDevelopmentStage)
6. **StartupProfile → TargetedMarket**: One-to-Many
7. **StartupProfile → CompanyMember**: One-to-Many
8. **StartupProfile → Stakeholder**: One-to-Many
9. **StartupProfile → Investor**: One-to-Many
10. **StartupProfile → Competitor**: One-to-Many
11. **StartupProfile → RevenueModel**: Many-to-Many (via StartupRevenueModel)
12. **StartupProfile → RevenueStream**: One-to-Many
13. **StartupProfile → FundingTarget**: One-to-One
14. **StartupProfile → RaisedFund**: One-to-Many

## Normalization Benefits

1. **Separation of Concerns**: Each app handles a specific domain
2. **Scalability**: Easy to add new features to specific domains
3. **Maintainability**: Clear separation makes code easier to maintain
4. **Performance**: Proper indexing and foreign key relationships
5. **Flexibility**: Admin-configurable options for stages and revenue models
6. **Data Integrity**: Foreign key constraints ensure data consistency

## File Structure

Each app follows the same structure:
```
app_name/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── model1.py
│   └── model2.py
├── serializers/
│   ├── __init__.py
│   ├── model1_serializer.py
│   └── model2_serializer.py
├── views/
│   ├── __init__.py
│   ├── model1_views.py
│   └── model2_views.py
└── admin.py
```

This structure ensures:
- **Readability**: Each operation is in separate files
- **Maintainability**: Easy to find and modify specific functionality
- **Scalability**: Easy to add new models and operations
- **Team Collaboration**: Clear separation allows multiple developers to work on different parts

