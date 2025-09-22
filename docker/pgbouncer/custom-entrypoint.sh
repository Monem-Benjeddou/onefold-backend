#!/bin/sh
set -e

# Create config directory if it doesn't exist
mkdir -p /etc/pgbouncer

# Generate pgbouncer.ini from environment variables
cat > /etc/pgbouncer/pgbouncer.ini <<EOF
[databases]
${DATABASES_DBNAME} = host=${DATABASES_HOST} port=${DATABASES_PORT} dbname=${DATABASES_DBNAME}

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = trust
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = session
max_client_conn = 100
default_pool_size = 25
admin_users = postgres
EOF

# Generate userlist.txt
cat > /etc/pgbouncer/userlist.txt <<EOF
"${DATABASES_USER}" "${DATABASES_PASSWORD}"
EOF

# Set proper permissions
chmod 644 /etc/pgbouncer/pgbouncer.ini
chmod 600 /etc/pgbouncer/userlist.txt

# Start pgbouncer
exec /usr/bin/pgbouncer /etc/pgbouncer/pgbouncer.ini