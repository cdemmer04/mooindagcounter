#!/bin/sh
# Wait for MariaDB to be reachable before starting Gunicorn.
# Inspired by the MXBentelo.nl entrypoint pattern.
set -e

_db_host="${DB_HOST:-localhost}"
_db_port="${DB_PORT:-3306}"
_db_wait_timeout="${DB_WAIT_TIMEOUT:-60}"
_db_wait_interval=2
_db_wait_elapsed=0

echo "Waiting for MariaDB at ${_db_host}:${_db_port} (timeout: ${_db_wait_timeout}s)..."
until nc -z "${_db_host}" "${_db_port}" 2>/dev/null; do
    if [ "${_db_wait_elapsed}" -ge "${_db_wait_timeout}" ]; then
        echo "Error: MariaDB at ${_db_host}:${_db_port} did not become reachable within ${_db_wait_timeout} seconds." >&2
        exit 1
    fi
    sleep "${_db_wait_interval}"
    _db_wait_elapsed=$((_db_wait_elapsed + _db_wait_interval))
done
echo "Database is up — starting Gunicorn."

exec gunicorn app:app \
    --bind "0.0.0.0:8080" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 30 \
    --pid /tmp/gunicorn.pid \
    --access-logfile - \
    --error-logfile -
