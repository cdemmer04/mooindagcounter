#!/bin/sh
# Wait for MariaDB to be reachable before starting Gunicorn.
# Inspired by the MXBentelo.nl entrypoint pattern.
set -e

_db_host="${DB_HOST:-localhost}"
_db_port="${DB_PORT:-3306}"

echo "Waiting for MariaDB at ${_db_host}:${_db_port}..."
until nc -z "${_db_host}" "${_db_port}" 2>/dev/null; do
    sleep 2
done
echo "Database is up — starting Gunicorn."

exec gunicorn app:app \
    --bind "0.0.0.0:8080" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -
