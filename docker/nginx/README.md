# KOLCT API Production Deployment Guide

This guide explains how to deploy the KOLCT API in production using your existing host nginx server.

## Overview

The production setup consists of:
- **kolct_backend**: Django API server (exposed on port 8000)
- **kolct_celery_worker**: Background task worker
- **kolct_db_prod**: PostgreSQL database (internal only)
- **kolct_redis**: Redis cache/queue (internal only)
- **Host Nginx**: Your existing nginx server acts as reverse proxy

## Quick Start

### 1. Build and Start Production Containers

```bash
# Build production images
make build-prod

# Start production services
make up-prod
```

### 2. Configure Host Nginx

Copy the sample configuration:
```bash
sudo cp docker/nginx/host-nginx-site.conf /etc/nginx/sites-available/kolct-api
```

Edit the configuration file:
```bash
sudo nano /etc/nginx/sites-available/kolct-api
```

Update these sections:
- Replace `yourdomain.com` with your actual domain
- Update the static files path: `/path/to/your/project/docker/static/`
- Update the media files path: `/path/to/your/project/docker/media/`
- Adjust the backend port if you changed `API_PORT` (default: 8000)

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/kolct-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 3. Run Initial Setup

```bash
# Run database migrations
make migrate-prod

# Collect static files
make collectstatic-prod

# Create admin user
make create-superuser-prod
```

## SSL/HTTPS Setup

After basic setup is working, enable SSL:

```bash
# Install SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Then in your nginx config:
1. Uncomment the HTTPS server block
2. Uncomment the HTTP to HTTPS redirect
3. Reload nginx: `sudo systemctl reload nginx`

## Production Management Commands

```bash
# View logs
make logs-backend-prod     # Backend logs
make logs-celery-prod      # Celery worker logs
make logs-db-prod          # Database logs

# Access Django shell
make shell-backend-prod

# Database operations
make migrate-prod
make collectstatic-prod
make create-superuser-prod

# Stop production services
make down-prod
```

## File Structure

```
docker/
├── static/           # Django static files (served by nginx)
├── media/            # User uploaded files (served by nginx)
└── nginx/
    ├── host-nginx-site.conf    # Sample nginx config
    └── README.md               # This file
```

## Environment Variables

Production uses these key environment variables from `.env`:

```env
ENV=0                           # Production mode
SECRET_KEY=your-secret-key      # Django secret key
DATABASE_NAME=kolct_production  # Production database name
API_PORT=8000                   # Backend port
ALLOWED_HOSTS=yourdomain.com    # Allowed domains
```

## Troubleshooting

### Backend not accessible
- Check if backend container is running: `docker ps | grep kolct_backend`
- Check backend logs: `make logs-backend-prod`
- Verify port mapping: Backend should be on `127.0.0.1:8009`

### Static files not loading
- Ensure static files are collected: `make collectstatic-prod`
- Check nginx config paths match actual directories
- Verify file permissions: `sudo chown -R www-data:www-data docker/static docker/media`

### Database connection issues
- Check database container: `docker ps | grep kolct_db_prod`
- Verify environment variables in `.env`
- Check database logs: `make logs-db-prod`

### SSL certificate issues
- Run certbot in verbose mode: `sudo certbot --nginx -v`
- Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Ensure domain DNS points to your server

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Regularly update your SSL certificates (certbot auto-renewal should handle this)
- Monitor logs for suspicious activity
- Keep Docker images updated by rebuilding regularly
- Use strong passwords for database and admin accounts

## Performance Optimization

- Enable nginx gzip compression
- Configure nginx caching for static files
- Monitor container resource usage: `docker stats`
- Scale celery workers if needed: adjust container count in docker-compose.prod.yml
- Consider using a CDN for static files in high-traffic scenarios 