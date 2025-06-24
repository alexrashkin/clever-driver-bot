#!/bin/bash

echo "=== Checking service status ==="
systemctl status driver

echo -e "\n=== Checking URL configuration ==="
echo "Root URLs:"
cat /opt/driver/urls.py

echo -e "\nAPI URLs:"
cat /opt/driver/api/urls.py

echo -e "\n=== Testing API endpoints ==="
echo "Testing toggle_tracking:"
curl -v http://localhost:8000/api/toggle_tracking/

echo -e "\nTesting location:"
curl -v "http://localhost:8000/api/location/?latitude=55.676803&longitude=37.52351"

echo -e "\n=== Restarting services ==="
systemctl restart driver
sleep 3

echo -e "\n=== Testing after restart ==="
curl -v http://localhost:8000/api/toggle_tracking/ 