RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up environment file for Kolct...${NC}"

if [ ! -f .env ]; then
	cat >.env <<EOL

ENV=1  
SECRET_KEY=$(openssl rand -hex 32)



DEV_ALLOWED_HOSTS=localhost,127.0.0.1
DEV_CSRF_TRUSTED_ORIGINS=http://localhost:8747,http://127.0.0.1:8747
DEV_VITE_API_URL=http://localhost:8747/api



PROD_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
PROD_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
PROD_VITE_API_URL=https://yourdomain.com/api


DATABASE_NAME=mydatabase
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_PORT=5432


REDIS_PORT=6379


API_PORT=8747
FRONTEND_PORT=5173


ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin


SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
GUNICORN=true


NODE_PACKAGE_MANAGER=pnpm


# Cards admin verification token (used to bypass tap_counter increment on verify)
CARDS_ADMIN_VERIFY_TOKEN=


POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=mydatabase
EOL
	echo -e "${GREEN}Created .env file${NC}"
	echo -e "${YELLOW}IMPORTANT: Update your domain and admin credentials in .env before deploying to production (ENV=0)${NC}"
else
	echo -e "${YELLOW}.env already exists, skipping...${NC}"
fi

echo -e "${GREEN}Environment setup complete!${NC}"
echo -e "${YELLOW}Remember to update your environment file with appropriate values before deploying.${NC}"

chmod +x docker/setup-env.sh
