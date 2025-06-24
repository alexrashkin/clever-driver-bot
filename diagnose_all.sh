#!/bin/bash

echo "=== Complete System Diagnosis ==="

echo "1. Service Status:"
echo "Driver service:"
systemctl status driver --no-pager
echo ""
echo "Nginx service:"
systemctl status nginx --no-pager

echo -e "\n2. Port Status:"
echo "Port 80 (HTTP):"
netstat -tulpn | grep :80
echo ""
echo "Port 8000 (Django):"
netstat -tulpn | grep :8000

echo -e "\n3. Nginx Configuration:"
nginx -t

echo -e "\n4. Django Status:"
cd /opt/driver
source venv/bin/activate
python manage.py check

echo -e "\n5. Testing Django directly:"
curl -v http://localhost:8000/ 2>&1 | head -10

echo -e "\n6. Testing Nginx:"
curl -v http://localhost/ 2>&1 | head -10

echo -e "\n7. Testing external access:"
curl -v http://194.87.236.174/ 2>&1 | head -10

echo -e "\n8. Nginx error logs:"
tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error log"

echo -e "\n9. Django logs:"
tail -n 10 /var/log/gunicorn/error.log 2>/dev/null || echo "No gunicorn error log"

echo "=== Diagnosis complete ===" 