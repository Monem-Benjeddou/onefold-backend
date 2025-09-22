#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKER_DIR="${PROJECT_ROOT}/docker"

echo "🚀 Setting up Docker volumes for static and media files..."

create_directory() {
	local dir_path="$1"
	local description="$2"

	if [ ! -d "$dir_path" ]; then
		echo "📁 Creating $description directory: $dir_path"
		mkdir -p "$dir_path"
		chmod 755 "$dir_path"
	else
		echo "✅ $description directory already exists: $dir_path"
	fi
}

echo ""
echo "🔧 Development Environment Setup:"

create_directory "${PROJECT_ROOT}/static" "static files (development)"
create_directory "${PROJECT_ROOT}/media" "media files (development)"
create_directory "${PROJECT_ROOT}/staticfiles" "collected static files (development)"

echo ""
echo "🔧 Production Environment Setup:"

create_directory "${DOCKER_DIR}/static" "static files (production host mount)"
create_directory "${DOCKER_DIR}/media" "media files (production host mount)"

if [ "${ENV:-1}" = "0" ]; then
	echo ""
	echo "🔧 Production Server Paths:"
	echo "ℹ️  Ensure these directories exist on production server:"
	echo "   - /var/www/static (for collected static files)"
	echo "   - /var/www/media (for uploaded media files)"
	echo "   - Run: sudo mkdir -p /var/www/{static,media} && sudo chown -R www-data:www-data /var/www"
fi

echo ""
echo "📋 Volume Mapping Summary:"
echo ""
echo "Development (ENV=1):"
echo "  Host: ${PROJECT_ROOT}/staticfiles <-> Container: /app/staticfiles"
echo "  Host: ${PROJECT_ROOT}/media <-> Container: /app/media"
echo "  Host: ${PROJECT_ROOT}/static <-> Container: /app/static"
echo ""
echo "Production (ENV=0):"
echo "  Host: ${DOCKER_DIR}/static <-> Container: /var/www/static"
echo "  Host: ${DOCKER_DIR}/media <-> Container: /var/www/media"
echo "  Host: ${PROJECT_ROOT}/static <-> Container: /app/static"
echo ""

echo "✅ Volume setup complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Copy .env.example to .env and configure your settings"
echo "   2. Run: docker-compose up -d"
echo "   3. Collect static files: docker exec kolct_django_dev_backend python manage.py collectstatic --noinput"
echo ""
