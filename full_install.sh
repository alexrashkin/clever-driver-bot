#!/bin/bash

echo "=== Complete Django Installation ==="

# Navigate to project directory
cd /opt/driver

# Remove old virtual environment
rm -rf venv

# Create new virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install django==5.2.3 djangorestframework==3.16.0 gunicorn==23.0.0

# Check Django configuration
echo "Checking Django configuration..."
python manage.py check

# Apply migrations
echo "Applying migrations..."
python manage.py makemigrations
python manage.py migrate

# Create initial data
echo "Creating initial data..."
python manage.py shell -c "
from driver.models import TrackingStatus
TrackingStatus.objects.get_or_create(id=1, defaults={'is_active': False})
print('Initial data created')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Set proper permissions
chmod -R 755 /opt/driver
chown -R root:root /opt/driver

# Restart services
echo "Restarting services..."
systemctl restart driver
sleep 3
systemctl restart nginx

# Check service status
echo "=== Service Status ==="
systemctl status driver --no-pager
echo ""
systemctl status nginx --no-pager

# Test the application
echo "=== Testing Application ==="
sleep 2
curl -s http://localhost:8000/ | head -10

echo "=== Installation Complete ===" 