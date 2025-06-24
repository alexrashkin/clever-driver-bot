#!/bin/bash

echo "=== Debugging 502 Bad Gateway ==="

echo "1. Checking if port 8000 is listening:"
netstat -tulpn | grep :8000

echo -e "\n2. Checking driver service status:"
systemctl status driver --no-pager

echo -e "\n3. Testing Django directly:"
curl -v http://localhost:8000/ 2>&1 | head -20

echo -e "\n4. Checking Django logs:"
tail -n 20 /var/log/gunicorn/error.log 2>/dev/null || echo "No gunicorn error log found"

echo -e "\n5. Checking if Django can start manually:"
cd /opt/driver
source venv/bin/activate
python manage.py check

echo -e "\n6. Testing API endpoint:"
curl -s http://localhost:8000/api/toggle_tracking/ -X POST -H 'Content-Type: application/json' -d '{"is_tracking": true}' || echo "API not responding"

echo -e "\n7. Checking nginx configuration:"
nginx -t

echo -e "\n8. Restarting services:"
systemctl restart driver
sleep 3
systemctl restart nginx
sleep 2

echo -e "\n9. Final test:"
curl -s http://localhost:8000/ | head -10 