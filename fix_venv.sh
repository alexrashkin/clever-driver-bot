#!/bin/bash

cd /opt/driver

# Remove existing venv
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install django==5.2.3
pip install djangorestframework==3.16.0
pip install gunicorn==23.0.0

# Verify installations
echo "=== Installed Packages ==="
pip list

# Test Django installation
echo "=== Django Test ==="
python3 -c "import django; print(f'Django version: {django.get_version()}')"

# Test DRF installation
echo "=== DRF Test ==="
python3 -c "import rest_framework; print('DRF import successful')"

# Test Gunicorn installation
echo "=== Gunicorn Test ==="
python3 -c "import gunicorn; print('Gunicorn import successful')"

# Apply migrations
echo "=== Applying Migrations ==="
python3 manage.py makemigrations
python3 manage.py migrate

# Collect static files
echo "=== Collecting Static Files ==="
python3 manage.py collectstatic --noinput

# Create initial tracking status
echo "=== Creating Initial Data ==="
python3 manage.py shell << EOF
from api.models import TrackingStatus
TrackingStatus.objects.get_or_create(id=1, defaults={'is_active': False})
EOF

# Restart services
echo "=== Restarting Services ==="
systemctl restart driver
systemctl status driver 