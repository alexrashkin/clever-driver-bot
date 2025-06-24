#!/bin/bash

echo "=== Manual Django Start ==="

cd /opt/driver
source venv/bin/activate

echo "Starting Django manually on port 8000..."
python manage.py runserver 0.0.0.0:8000 &

sleep 5

echo "Testing Django..."
curl -s http://localhost:8000/ | head -10

echo "Testing API..."
curl -s http://localhost:8000/api/toggle_tracking/ -X POST -H 'Content-Type: application/json' -d '{"is_tracking": true}'

echo "Stopping manual server..."
pkill -f "runserver"

echo "=== Manual start complete ===" 