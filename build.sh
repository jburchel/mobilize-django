#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create superuser using the management command
python manage.py create_default_superuser

echo "Build complete!"