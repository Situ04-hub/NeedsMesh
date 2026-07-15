#!/usr/bin/env bash
# exit on error
set -o errexit

# Run database migrations
python manage.py migrate

# Automatically create a superuser
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@needsmesh.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# Start Gunicorn
gunicorn NeedsMesh.wsgi:application
