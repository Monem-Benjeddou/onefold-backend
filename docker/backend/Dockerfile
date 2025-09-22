# === Base Stage ===
# Use a specific slim image version for reproducibility
FROM python:3.11-slim-bookworm AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies required for packages like psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/docker

# Set Python path to include both /app and /app/api
ENV PYTHONPATH=/app:/app/api:$PYTHONPATH

# Install Python dependencies
# Copy requirements first to leverage Docker cache
COPY api/requirements.txt /app/requirements.txt

# Upgrade pip and install dependencies in one layer for better caching
RUN pip install --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt


# === Development Stage ===
FROM base AS development

# Get the ENV arg for target selection
ARG ENV=1
ENV ENV=1

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/docker

# Copy entrypoint scripts to the container
COPY docker/backend/entrypoint.sh /app/docker/entrypoint.sh
COPY docker/backend/entrypoint-beat.sh /app/docker/entrypoint-beat.sh
COPY docker/backend/wait-for-postgres.sh /app/docker/wait-for-postgres.sh

# Make scripts executable
RUN chmod +x /app/docker/entrypoint.sh \
    && chmod +x /app/docker/entrypoint-beat.sh \
    && chmod +x /app/docker/wait-for-postgres.sh

# Expose port for development server
EXPOSE 8000

# Set environment variable for .env file path
ENV ENV_FILE_PATH=.env

# Default command to run django development server
CMD ["sh", "/app/docker/entrypoint.sh"]

# === Production Stage ===
FROM base AS production

# Get the ENV arg for target selection
ARG ENV=0
ENV ENV=0

# Create a non-root user and group
RUN addgroup --system app && adduser --system --ingroup app appuser

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/docker

# Copy entrypoint scripts to the container
COPY docker/backend/entrypoint.sh /app/docker/entrypoint.sh
COPY docker/backend/entrypoint-beat.sh /app/docker/entrypoint-beat.sh
COPY docker/backend/wait-for-postgres.sh /app/docker/wait-for-postgres.sh

# Make scripts executable
RUN chmod +x /app/docker/entrypoint.sh \
    && chmod +x /app/docker/entrypoint-beat.sh \
    && chmod +x /app/docker/wait-for-postgres.sh

# Install production-specific dependencies
RUN pip install --no-cache-dir gunicorn

# Set ownership of application code
RUN chown -R appuser:app /app

# Switch to non-root user
USER appuser

# Expose port for Gunicorn
EXPOSE 8000

# Set environment variable for .env file path
ENV ENV_FILE_PATH=.env

# Run with entrypoint script for migrations and then Gunicorn
CMD ["sh", "/app/docker/entrypoint.sh"] 