until cd /app; do
	echo "Waiting for server volume..."
done

check_postgres() {
	nc -z -w 5 $DATABASE_HOST 5432
	return $?
}

echo "Waiting for PostgreSQL at $DATABASE_HOST:5432..."
until check_postgres; do
	echo "PostgreSQL is unavailable - sleeping"
	sleep 2
done

echo "PostgreSQL is accepting connections"

echo "Waiting for API at api:$API_PORT..."
until nc -z -w 5 kolct_backend $API_PORT; do
	echo "API is unavailable - sleeping"
	sleep 2
done

echo "API is up"

echo "Starting celery beat..."
celery -A config beat -l INFO
