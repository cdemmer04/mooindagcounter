#!/bin/sh
# Start Gunicorn immediately.
# DB availability is handled gracefully by the app (db_offline.html).
# A separate health-check on /healthz will reflect DB status.
set -e

export TZ="${TZ:-Europe/Amsterdam}"
export HOME=/tmp

echo "Starting Gunicorn (TZ=${TZ})..."

exec gunicorn app:app \
    --bind "0.0.0.0:8080" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 30 \
    --pid /tmp/gunicorn.pid \
    --worker-tmp-dir /tmp \
    --access-logfile - \
    --error-logfile -
