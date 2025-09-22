# Docker Configuration Structure

This directory contains all Docker-related configuration for Kolct application.

## Structure

- `docker-compose.yml` - Main development configuration
- `docker-compose.prod.yml` - Production override configuration
- `docker-compose.gpu.yml` - GPU support override configuration
- `backend/` - Backend service configuration
- `frontend/` - Frontend service configuration
- `nginx/` - Nginx configuration for production

## Usage

All Docker Compose commands should use files from this directory. The Makefile has been updated to reflect these paths.

### Development

```bash
# Start development environment
make up

# Start with GPU acceleration for Ollama
make up-gpu

# Check status of containers
make status

# Get logs from a specific service
make logs SERVICE=backend
```

### Production

```bash
# Start production environment
make up-prod

# Stop production environment
make down-prod
```

### Accessing containers

```bash
# Get interactive shell in backend container
make it-backend

# Access Django shell
make shell-backend
```

## Docker Compose Files

### docker-compose.yml

The main Docker Compose file that defines all services for development environment.

### docker-compose.prod.yml

Production override for Docker Compose. Key differences:
- Uses production targets in Dockerfiles
- Different database settings (no exposed ports)
- Enables Nginx for serving static files and SSL
- Includes Certbot for SSL certificates
- Disables Ollama services in production

### docker-compose.gpu.yml

GPU override for Docker Compose that enables NVIDIA GPU acceleration for Ollama:
- Configures Ollama container with NVIDIA runtime
- Sets environment variables for GPU visibility
- Increases memory and CPU limits for backend processing

## Note on Backward Compatibility

For backward compatibility, placeholder files are maintained in the project root directory, but all new development should use the files in this directory.

## GPU Support

### Platform-Specific GPU Support

The Docker configuration has been updated to support different GPU types:

- **Apple Silicon Macs**: Uses Metal API for acceleration via `OLLAMA_USE_METAL=true`
- **Intel Macs**: Limited GPU support with CPU fallback
- **Linux with NVIDIA**: Full CUDA acceleration via NVIDIA Container Toolkit

### Troubleshooting GPU Issues

#### For Mac Users

If you're using a Mac and encounter the following error:

```
Error response from daemon: could not select device driver "nvidia" with capabilities: [[gpu]]
```

This happens because the default configuration is trying to use NVIDIA drivers that aren't available on Macs. Use the Mac-specific GPU configuration instead:

```bash
# Check your GPU type
make detect-gpu

# Start with Mac-specific GPU support
make up-gpu

# Test GPU acceleration on Mac
make test-mac-gpu
```

#### For Linux/NVIDIA Users

If you encounter GPU issues on Linux:

1. Make sure NVIDIA drivers are installed: `nvidia-smi`
2. Verify NVIDIA Docker support: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`
3. Check the logs: `docker logs ollama`

For more details, see `docs/ollama-gpu-setup.md`.

# Docker Configuration for Kolct

This document provides comprehensive instructions for setting up, configuring, and running Kolct project using Docker. This setup follows industry best practices for Django and React applications with security, scalability, and maintainability in mind.

## Technology Stack

- **Backend**: Django 4.2 with Django REST Framework
- **Frontend**: React 18 with TypeScript, Redux, and Vite
- **Database**: PostgreSQL 13
- **Cache**: Redis
- **Task Queue**: Celery
- **Web Server**: Nginx
- **Package Manager**: pnpm

## Directory Structure

```
docker/
├── backend/           # Django backend Docker configuration
├── frontend/          # React frontend Docker configuration
├── nginx/             # Nginx configuration for production
├── setup-env.sh       # Environment setup script
└── README.md          # This documentation
```

## Prerequisites

- Docker Engine (20.10.0+)
- Docker Compose (2.0.0+)
- Make

## Initial Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:yourorganization/kolct-api.neothons.com.git
   cd kolct-api.neothons.com
   ```

2. Generate environment files:
   ```bash
   make setup
   ```
   This creates `.env.dev` and `.env.prod` files with default configurations.

3. Review and customize the environment variables in `.env.dev` and `.env.prod` as needed.

## Development Environment

The development environment is configured for rapid iteration with hot-reloading, debug tools, and direct access to logs.

### Starting the Development Environment

```bash
make up
```

This command:
- Builds and starts all required containers
- Sets up database and Redis connections
- Starts the Django development server
- Starts the Vite dev server with hot module replacement
- Configures Celery workers for background tasks

### Development URLs

- **Django API**: http://localhost:8747
- **Django Admin**: http://localhost:8747/admin/
- **React App**: http://localhost:5173
- **API Documentation**: http://localhost:8747/api/docs/
- **Storybook**: http://localhost:6006

### Common Development Tasks

```bash
# View logs from all services
make logs

# View logs from a specific service
make logs SERVICE=backend
make logs-frontend  # Shortcut for frontend logs

# Access Django shell
make shell-backend

# Interactive backend terminal
make it-backend

# Frontend shell
make shell-frontend

# Run migrations
make migrate

# Create superuser
make create-superuser

# Collect static files
make collectstatic

# Run tests
make test
make test-backend
make test-frontend
make test-file path=apps/accounts/tests/test_auth.py

# Run linters
make lint
```

## Frontend Development

The frontend is built with React, TypeScript, and Vite. The development server is configured with hot module replacement for a smooth development experience.

### Key Frontend Features

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast development server and build tool
- **TailwindCSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **React Query**: Data fetching and caching
- **Axios**: HTTP client
- **Storybook**: Component development and documentation

### Storybook

Storybook is included for component development, testing, and documentation. It provides an isolated environment to develop UI components without the need for a running backend.

#### Running Storybook

Storybook is automatically started as part of the development environment and is available at http://localhost:6006.

You can also run it separately:

```bash
# Inside the ui directory
pnpm run storybook

# Or using Docker
docker-compose up storybook
```

#### Component Organization

UI components are organized in a modular folder structure:

```
ui/src/components/ui/
├── button/
│   ├── button.tsx
│   ├── button.stories.tsx
│   └── index.ts
├── card/
│   ├── card.tsx
│   ├── card.stories.tsx
│   └── index.ts
└── ...
```

Each component has:
- A dedicated folder
- The component implementation file
- A stories file for Storybook
- An index.ts file for clean exports

## Production Environment

The production setup is optimized for security, performance, and reliability.

### Building Production Images

```bash
make build-prod
```

### Starting Production Environment

```bash
make up-prod
```

### SSL Certificate Setup

```bash
export DOMAIN=yourdomain.com
make install-cert
```

## Database Management

```bash
# Create a database backup
make db-backup

# Create a backup with a custom filename
make db-backup BACKUP_FILE=custom_name.sql

# Restore from a backup
make db-backup BACKUP_FILE=your_backup.sql
```

## Makefile Reference

The project includes a comprehensive Makefile to streamline common operations:

### Setup Commands
- `make setup` - Generate environment files
- `make help` - Display available commands

### Development Commands
- `make build-dev` - Build development images
- `make up` - Start development environment
- `make down` - Stop development environment
- `make logs` - View container logs
- `make shell-backend` - Access Django shell
- `make shell-frontend` - Access frontend shell
- `make migrate` - Run Django migrations
- `make create-superuser` - Create Django admin user
- `make collectstatic` - Collect static files

### Production Commands
- `make build-prod` - Build production images
- `make up-prod` - Start production environment
- `make down-prod` - Stop production environment
- `make install-cert` - Install SSL certificate

### Testing Commands
- `make lint` - Run code linters
- `make test` - Run all tests
- `make test-backend` - Run backend tests
- `make test-frontend` - Run frontend tests
- `make test-file path=path/to/test.py` - Run specific test file

### Cleanup Commands
- `make clean` - Remove all containers, volumes, and networks

## Frontend Package Management

This project uses pnpm for frontend package management:

```bash
# To add a new dependency
make shell-frontend
pnpm add package-name

# To add a dev dependency
pnpm add -D package-name

# To update dependencies
pnpm update
```

## Security Considerations

This setup incorporates several security best practices:
- Non-root users in containers
- Separate networks for frontend/backend communication
- Environment-based configuration
- Secret management via environment variables
- Proper SSL/TLS configuration in production
- CSRF protection
- Rate limiting for sensitive endpoints
- Regular security updates via Docker images

## Troubleshooting

If you encounter issues:

1. Check logs with `make logs`
2. Ensure ports 5173, 8747, 5432, and 6379 are available
3. Verify environment variables in `.env.dev` or `.env.prod`
4. Restart containers with `make down && make up`
5. For persistent issues, rebuild with `make build-dev && make up`

## Contribution Guidelines

When contributing to this project:
1. Follow the established code structure
2. Write tests for new features
3. Document changes in appropriate README files
4. Follow the Django REST Framework best practices
5. Use React hooks and functional components
6. Maintain type safety with TypeScript
