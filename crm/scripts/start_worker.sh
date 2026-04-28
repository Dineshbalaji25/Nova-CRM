#!/bin/sh

set -e

# Wait for DB (Workers also need DB)
echo "Waiting for postgres..."
while ! nc -z db_new 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Start Celery
exec celery -A config worker --loglevel=info
