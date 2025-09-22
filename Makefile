# ================================================
# Noev Backend - Docker Workflow (kolct-style)
# ================================================

.PHONY: help up down down-v restart force-restart status logs logs-backend logs-db logs-redis logs-celery logs-beat shell-backend it-backend migrate collectstatic create-superuser db-backup db-restore env-info

# Project configuration
PROJECT_NAME := noev
ENV_FILE ?= .env
CONTAINER_SUFFIX ?= $(shell grep "^CONTAINER_SUFFIX=" $(ENV_FILE) 2>/dev/null | cut -d= -f2 || echo "dev")
COMPOSE_PROJECT := $(PROJECT_NAME)-$(CONTAINER_SUFFIX)

# Compose wrapper
COMPOSE = docker compose -p $(COMPOSE_PROJECT) --env-file $(ENV_FILE) -f docker/docker-compose.yml

# Service names (must match docker-compose.yml)
BACKEND_SERVICE = web
DB_SERVICE = db
REDIS_SERVICE = redis
CELERY_SERVICE = worker
CELERY_BEAT_SERVICE = beat

help:
	@echo "Noev Backend - Docker Workflow"
	@echo "Usage: make [TARGET] [ENV_FILE=.env] [CONTAINER_SUFFIX=dev]"
	@echo "Targets: up, up-fast, down, down-fast, down-v, restart, force-restart, status, logs, logs-backend, logs-db, logs-redis, logs-celery, logs-beat, shell-backend, it-backend, migrate, collectstatic, create-superuser, db-backup BACKUP_FILE=..., db-restore BACKUP_FILE=..., env-info"
	@echo "Fast Development: up-fast (minimal deps), down-fast"
	@echo "Extra: manage CMD=..., exec CMD=..., seed-users COUNT=10, test"

env-info:
	@echo "Project: $(PROJECT_NAME)"
	@echo "Compose Project: $(COMPOSE_PROJECT)"
	@echo "ENV_FILE: $(ENV_FILE)"

up:
	$(COMPOSE) up -d
	@echo "Backend: http://localhost:8000"
	@echo "Docs:    http://localhost:8000/api/docs/"

up-fast:
	docker compose -f docker-compose.dev.yml up -d --build
	@echo "Backend: http://localhost:8009"
	@echo "Fast development mode with minimal dependencies"

down:
	$(COMPOSE) down

down-fast:
	docker compose -f docker-compose.dev.yml down

down-v:
	$(COMPOSE) down -v

status:
	$(COMPOSE) ps

restart:
	$(COMPOSE) stop
	$(COMPOSE) up -d

force-restart:
	$(COMPOSE) down --remove-orphans || true
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f

logs-backend:
	$(COMPOSE) logs -f $(BACKEND_SERVICE)

logs-db:
	$(COMPOSE) logs -f $(DB_SERVICE)

logs-redis:
	$(COMPOSE) logs -f $(REDIS_SERVICE)

logs-celery:
	$(COMPOSE) logs -f $(CELERY_SERVICE)

logs-beat:
	$(COMPOSE) logs -f $(CELERY_BEAT_SERVICE)

shell-backend:
	$(COMPOSE) exec $(BACKEND_SERVICE) python manage.py shell

it-backend:
	$(COMPOSE) exec -it $(BACKEND_SERVICE) bash

migrate:
	$(COMPOSE) exec $(BACKEND_SERVICE) python api/manage.py migrate

collectstatic:
	$(COMPOSE) exec $(BACKEND_SERVICE) python api/manage.py collectstatic --noinput

create-superuser:
	$(COMPOSE) exec $(BACKEND_SERVICE) python api/manage.py createsuperuser

# Generic manage.py runner
manage:
	@[ -n "$(CMD)" ] || (echo "Error: Provide CMD=... (e.g., makemigrations app)" && exit 1)
	$(COMPOSE) exec $(BACKEND_SERVICE) python api/manage.py $(CMD)

# Exec arbitrary command in web
exec:
	@[ -n "$(CMD)" ] || (echo "Error: Provide CMD=..." && exit 1)
	$(COMPOSE) exec $(BACKEND_SERVICE) sh -lc "$(CMD)"

# Run pytest in web container
test:
	$(COMPOSE) exec $(BACKEND_SERVICE) pytest

# Seed users
seed-users:
	$(COMPOSE) exec $(BACKEND_SERVICE) python api/manage.py seed_users $(COUNT)

db-backup:
	@[ -n "$(BACKUP_FILE)" ] || (echo "Error: Provide BACKUP_FILE=..." && exit 1)
	$(COMPOSE) exec $(DB_SERVICE) pg_dump -U $$DATABASE_USER $$DATABASE_NAME > $(BACKUP_FILE)
	@echo "Backup saved to $(BACKUP_FILE)"

db-restore:
	@[ -n "$(BACKUP_FILE)" ] || (echo "Error: Provide BACKUP_FILE=..." && exit 1)
	@echo "WARNING: This will overwrite the database"
	@read -p "Continue? (y/n) " confirm; \
	if [ "$$confirm" = "y" ]; then \
		cat $(BACKUP_FILE) | $(COMPOSE) exec -T $(DB_SERVICE) psql -U $$DATABASE_USER $$DATABASE_NAME; \
		echo "Restore completed"; \
	else \
		echo "Restore cancelled"; \
	fi


