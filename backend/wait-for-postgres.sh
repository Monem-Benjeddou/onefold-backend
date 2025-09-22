set -e

host="$1"
shift
port="${DATABASE_INTERNAL_PORT:-5432}"
shift
user="$1"
shift
password="$1"
shift
cmd="$@"

check_postgres() {
	nc -z -w 5 "$host" "$port"
	return $?
}

echo "Waiting for PostgreSQL at $host:$port..."
until check_postgres; do
	>&2 echo "PostgreSQL is unavailable - sleeping"
	sleep 2
done

>&2 echo "PostgreSQL is up - executing command"
exec $cmd
