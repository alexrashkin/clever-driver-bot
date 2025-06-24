#!/bin/bash

echo "=== Current Status ==="
echo "Driver service:"
systemctl status driver --no-pager

echo -e "\nNginx service:"
systemctl status nginx --no-pager

echo -e "\n=== Checking Django ==="
cd /opt/driver

if [ -d "venv" ]; then
    echo "Virtual environment exists"
    source venv/bin/activate
    python manage.py check
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install django==5.2.3 djangorestframework==3.16.0 gunicorn==23.0.0
    python manage.py check
fi

echo -e "\n=== Testing API ==="
curl -s http://localhost:8000/api/toggle_tracking/ || echo "API not responding" 