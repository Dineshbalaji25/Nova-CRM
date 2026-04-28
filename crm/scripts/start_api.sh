#!/bin/sh

set -e

# Wait for DB
echo "Waiting for postgres..."
while ! nc -z db_new 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Migrate
python manage.py migrate

# Collect Static
python manage.py collectstatic --noinput

# Start Server
exec python manage.py runserver 0.0.0.0:8000
