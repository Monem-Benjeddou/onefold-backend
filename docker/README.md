# Nevo Backend Docker Setup

This directory contains the Docker configuration for the Nevo Backend application.

## Quick Start

1. **Create a `.env` file** in the project root with the following variables:
```bash
# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=nevo_db
DATABASE_HOST=nevo_db
DATABASE_PORT=5432

# API Configuration
API_PORT=8009

# Admin Configuration
ADMIN_EMAIL=admin@admin.com
ADMIN_PASSWORD=admin12345

# Docker Configuration
PROJECT_NAME=nevo
CONTAINER_SUFFIX=dev
```

2. **Start the services**:
```bash
cd docker
docker-compose up -d
```

3. **Access the application**:
- API: http://localhost:8009
- Admin: http://localhost:8009/admin
- API Docs: http://localhost:8009/api/schema/swagger-ui/

## Services

- **nevo-backend**: Django application server
- **nevo_db**: PostgreSQL database
- **nevo_redis**: Redis cache and message broker
- **nevo_celery_worker**: Celery worker for background tasks
- **nevo_celery_beat**: Celery beat scheduler
- **pgbouncer**: PostgreSQL connection pooler

## Development

The application runs in development mode by default with hot reloading enabled. The Django development server will automatically reload when you make changes to the code.

## Production

To run in production mode, set the following environment variables:
```bash
BACKEND_TARGET=production
ENV=0
GUNICORN=true
```

## Troubleshooting

1. **Database connection issues**: Make sure PostgreSQL is running and accessible
2. **Permission issues**: Check that the Docker volumes have proper permissions
3. **Port conflicts**: Ensure ports 8009, 5432, and 6380 are available

## Commands

- **View logs**: `docker-compose logs -f nevo-backend`
- **Restart service**: `docker-compose restart nevo-backend`
- **Stop all services**: `docker-compose down`
- **Rebuild and start**: `docker-compose up --build`