#!/bin/bash

echo "=== Quick Fix for Django ==="

cd /opt/driver

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
pip install django==5.2.3 gunicorn==23.0.0

# Check Django
echo "Checking Django..."
python manage.py check

# Start manually to see errors
echo "Starting Django manually..."
python manage.py runserver 0.0.0.0:8000 &
sleep 5

# Test
echo "Testing..."
curl -s http://localhost:8000/ | head -5

# Stop manual server
pkill -f "runserver"

echo "=== Quick fix complete ===" 