#!/usr/bin/env bash
set -e

PORT="${PORT:-7860}"

echo "==> Running database migrations..."
python manage.py migrate --noinput || echo "Warning: Migration failed or skipped"

echo "==> Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed"

echo "==> Starting Gunicorn server on port ${PORT}..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --workers 2 --timeout 120
