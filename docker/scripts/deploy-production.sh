#!/bin/bash

# Production Deployment Script for KOLCT
# This script deploys KOLCT in production mode using Neon.com database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

echo -e "${BLUE}🚀 KOLCT Production Deployment${NC}"
echo "=================================="

# Check if production environment file exists
PROD_ENV_FILE="$PROJECT_ROOT/.env.production"
if [ ! -f "$PROD_ENV_FILE" ]; then
	echo -e "${YELLOW}⚠️  Production environment file not found${NC}"
	echo "Creating from template..."

	if [ -f "$PROJECT_ROOT/.env.production.example" ]; then
		cp "$PROJECT_ROOT/.env.production.example" "$PROD_ENV_FILE"
		echo -e "${GREEN}✅ Created .env.production from template${NC}"
		echo -e "${YELLOW}📝 Please edit .env.production with your production values${NC}"
		echo "   Especially set NEON_DATABASE_URL with your Neon.com database URL"
		exit 1
	else
		echo -e "${RED}❌ No production environment template found${NC}"
		exit 1
	fi
fi

# Check if NEON_DATABASE_URL is set
if ! grep -q "^NEON_DATABASE_URL=" "$PROD_ENV_FILE" || grep -q "^NEON_DATABASE_URL=$" "$PROD_ENV_FILE"; then
	echo -e "${RED}❌ NEON_DATABASE_URL not set in .env.production${NC}"
	echo "Please set your Neon.com database URL in .env.production"
	echo "Example: NEON_DATABASE_URL=postgresql://user:pass@host/db?sslmode=require"
	exit 1
fi

echo -e "${GREEN}✅ Production environment file found${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
	echo -e "${RED}❌ Docker is not running${NC}"
	echo "Please start Docker and try again"
	exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
	echo -e "${RED}❌ docker-compose not found${NC}"
	echo "Please install docker-compose and try again"
	exit 1
fi

echo -e "${GREEN}✅ docker-compose is available${NC}"

# Stop any existing production containers
echo -e "${BLUE}🛑 Stopping existing production containers...${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker/docker-compose.prod.yml down --remove-orphans || true

# Pull latest images
echo -e "${BLUE}📥 Pulling latest images...${NC}"
docker-compose -f docker/docker-compose.prod.yml pull || true

# Build production images
echo -e "${BLUE}🔨 Building production images...${NC}"
docker-compose -f docker/docker-compose.prod.yml build --no-cache

# Start production services
echo -e "${BLUE}🚀 Starting production services...${NC}"
docker-compose -f docker/docker-compose.prod.yml --env-file .env.production up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "${BLUE}🔍 Checking service health...${NC}"

# Check backend service
if docker ps | grep -q "kolct_django_prod_backend"; then
	echo -e "${GREEN}✅ Backend service is running${NC}"
else
	echo -e "${RED}❌ Backend service failed to start${NC}"
	echo "Checking logs..."
	docker logs kolct_django_prod_backend --tail 20
	exit 1
fi

# Check Redis service
if docker ps | grep -q "kolct_redis_prod"; then
	echo -e "${GREEN}✅ Redis service is running${NC}"
else
	echo -e "${RED}❌ Redis service failed to start${NC}"
	echo "Checking logs..."
	docker logs kolct_redis_prod --tail 20
	exit 1
fi

# Check Celery worker
if docker ps | grep -q "kolct_celery_prod_worker"; then
	echo -e "${GREEN}✅ Celery worker is running${NC}"
else
	echo -e "${RED}❌ Celery worker failed to start${NC}"
	echo "Checking logs..."
	docker logs kolct_celery_prod_worker --tail 20
	exit 1
fi

# Test database connection
echo -e "${BLUE}🔍 Testing database connection...${NC}"
if docker exec kolct_django_prod_backend python scripts/test_neon_config.py >/dev/null 2>&1; then
	echo -e "${GREEN}✅ Database connection successful${NC}"
else
	echo -e "${YELLOW}⚠️  Database connection test failed${NC}"
	echo "This might be expected if using example credentials"
	echo "Please check your NEON_DATABASE_URL configuration"
fi

# Show running services
echo -e "${BLUE}📋 Running services:${NC}"
docker-compose -f docker/docker-compose.prod.yml ps

# Show service URLs
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo "Backend API: http://localhost:8009"
echo "Admin Panel: http://localhost:8009/admin/"

# Show logs command
echo -e "${BLUE}📝 To view logs:${NC}"
echo "docker-compose -f docker/docker-compose.prod.yml logs -f"

# Show stop command
echo -e "${BLUE}🛑 To stop services:${NC}"
echo "docker-compose -f docker/docker-compose.prod.yml down"

echo -e "${GREEN}🎉 Production deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Configure your reverse proxy (nginx) to point to port 8009"
echo "2. Set up SSL certificates for your domain"
echo "3. Configure monitoring and logging"
echo "4. Set up backup procedures"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "- Production Database Guide: docs/deployment/production-database.md"
echo "- Neon Setup Guide: docs/database/neon-setup.md"
