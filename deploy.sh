#!/bin/bash

echo "🚀 Starting comprehensive database synchronization and debugging..."
python manage.py comprehensive_schema_sync --verbose

echo "🔧 Fixing migration state for columns that already exist..."
python manage.py fix_migration_state

echo "Running Django migrations..."
python manage.py migrate --run-syncdb

echo "Creating Celery tables..."
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results

echo "Creating cache table..."
python manage.py createcachetable

echo "Fixing data type mismatches..."
python manage.py fix_supabase_data_types

echo "🔧 Fixing people table schema mismatch..."
python manage.py fix_people_table_schema

echo "🔍 Running production queryset debugging..."
python manage.py debug_production_queryset

echo "Creating default superuser..."
python manage.py create_default_superuser

# Promote specific user to superuser if email is provided
if [ ! -z "$PROMOTE_USER_EMAIL" ]; then
    echo "Promoting user $PROMOTE_USER_EMAIL to superuser..."
    python manage.py make_user_superuser "$PROMOTE_USER_EMAIL" || true
fi

# Assign user to office if email and office are provided
if [ ! -z "$ASSIGN_USER_EMAIL" ] && [ ! -z "$ASSIGN_USER_OFFICE" ]; then
    echo "Assigning user $ASSIGN_USER_EMAIL to office $ASSIGN_USER_OFFICE..."
    python manage.py assign_user_to_office "$ASSIGN_USER_EMAIL" --office-name="$ASSIGN_USER_OFFICE" --role="${ASSIGN_USER_ROLE:-standard_user}" || true
fi

echo "Starting gunicorn server..."
gunicorn mobilize.wsgi:application