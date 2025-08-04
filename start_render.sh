#!/bin/bash

# Render.com startup script for Mobilize CRM
# This script handles database setup and starts the application with optimized Gunicorn settings

set -e  # Exit on any error

echo "=== Starting Mobilize CRM Deployment ==="

# Database setup and migrations
echo "1. Running database schema sync..."
python manage.py comprehensive_schema_sync --verbose

echo "2. Fixing Supabase data types..."
python manage.py fix_supabase_data_types

echo "3. Running Django migrations..."
python manage.py migrate

echo "4. Checking Celery migrations..."
python manage.py showmigrations django_celery_beat
python manage.py showmigrations django_celery_results

echo "5. Creating cache table..."
python manage.py createcachetable

echo "6. Compressing static files..."
python manage.py compress

echo "7. Starting Gunicorn with optimized configuration..."
exec gunicorn --config gunicorn.conf.py mobilize.wsgi:application