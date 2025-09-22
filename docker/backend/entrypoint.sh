#!/bin/bash
set -e

echo "🚀 Starting Nevo Backend..."

# Change to the api directory where manage.py is located
cd /app/api

# Set default values
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@admin.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin12345}
DATABASE_HOST=${DATABASE_HOST:-nevo_db}
API_PORT=${API_PORT:-8009}

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
until nc -z -w 5 $DATABASE_HOST 5432; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Run migrations
echo "🔄 Applying database migrations..."
python manage.py migrate --noinput

# Create admin user
echo "👤 Creating admin user..."
python manage.py shell -c "
import os
import django
from django.db import IntegrityError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.user.models import User

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@admin.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin12345')

admin = User.objects.filter(email=ADMIN_EMAIL).first()
if not admin:
    print(f'Creating admin user: {ADMIN_EMAIL}')
    admin = User.objects.create_superuser(
        is_email_verified=True, 
        username='admin', 
        email=ADMIN_EMAIL, 
        password=ADMIN_PASSWORD
    )
    print('✅ Admin user created')
else:
    print('Admin user already exists')
"

# Start server
echo "🌐 Starting server on port $API_PORT..."
if [ "$GUNICORN" = "true" ]; then
    exec gunicorn --bind 0.0.0.0:$API_PORT --workers 3 -k uvicorn.workers.UvicornWorker config.asgi:application
else
    exec python manage.py runserver 0.0.0.0:$API_PORT
fi