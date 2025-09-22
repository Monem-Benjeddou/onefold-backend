FROM pgbouncer/pgbouncer:latest

# Switch to root user to handle permissions
USER root

# Create necessary directories with proper permissions
RUN mkdir -p /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer && \
    chmod 755 /etc/pgbouncer && \
    chmod 755 /var/log/pgbouncer && \
    chmod 755 /var/run/pgbouncer

# Copy configuration files (these will be overridden by volumes but needed for build)
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY userlist.txt /etc/pgbouncer/userlist.txt

# Create a startup script to handle permissions at runtime
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Fix permissions for mounted volumes' >> /entrypoint.sh && \
    echo 'if [ -f /etc/pgbouncer/pgbouncer.ini ]; then' >> /entrypoint.sh && \
    echo '    chmod 644 /etc/pgbouncer/pgbouncer.ini' >> /entrypoint.sh && \
    echo 'fi' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'if [ -f /etc/pgbouncer/userlist.txt ]; then' >> /entrypoint.sh && \
    echo '    chmod 600 /etc/pgbouncer/userlist.txt' >> /entrypoint.sh && \
    echo 'fi' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Ensure directories have correct permissions' >> /entrypoint.sh && \
    echo 'chown -R 999:999 /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Switch to pgbouncer user and run pgbouncer' >> /entrypoint.sh && \
    echo 'exec su-exec 999:999 /opt/pgbouncer/pgbouncer /etc/pgbouncer/pgbouncer.ini' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Install su-exec for proper user switching
RUN apk add --no-cache su-exec

# Expose PgBouncer port
EXPOSE 6432

# Use the custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]