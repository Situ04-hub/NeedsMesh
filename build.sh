#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate

# Automatically create a superuser (for free-tier hosting where shell isn't available)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@needsmesh.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

