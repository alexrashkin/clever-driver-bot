#!/bin/bash

echo "=== Setting up Django project ==="

# Navigate to project directory
cd /opt/driver

# Remove old virtual environment if exists
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install django==5.2.3 djangorestframework==3.16.0 gunicorn==23.0.0

# Check Django configuration
echo "=== Checking Django configuration ==="
python manage.py check

# Apply migrations
echo "=== Applying migrations ==="
python manage.py makemigrations
python manage.py migrate

# Create initial data
echo "=== Creating initial data ==="
python manage.py shell -c "
from driver.models import TrackingStatus
TrackingStatus.objects.get_or_create(id=1, defaults={'is_tracking': False})
print('Initial data created')
"

# Collect static files
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

# Set proper permissions
chmod -R 755 /opt/driver
chown -R root:root /opt/driver

# Restart services
echo "=== Restarting services ==="
systemctl restart driver
systemctl restart nginx

# Check service status
echo "=== Service status ==="
systemctl status driver
systemctl status nginx

echo "=== Installation complete ===" 