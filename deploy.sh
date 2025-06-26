#!/bin/bash

echo "🚀 Starting comprehensive database synchronization and debugging..."
python manage.py comprehensive_schema_sync --verbose

echo "Running Django migrations..."
python manage.py migrate --run-syncdb

echo "Creating Celery tables..."
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results

echo "Creating cache table..."
python manage.py createcachetable

echo "Fixing data type mismatches..."
python manage.py fix_supabase_data_types

echo "🔍 Running production queryset debugging..."
python manage.py debug_production_queryset

echo "Starting gunicorn server..."
gunicorn mobilize.wsgi:application