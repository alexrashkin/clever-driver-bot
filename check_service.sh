#!/bin/bash

# Check service status
echo "=== Service Status ==="
systemctl status driver

# Check Gunicorn logs
echo "=== Gunicorn Error Log ==="
tail -n 50 /var/log/gunicorn/error.log

echo "=== Gunicorn Access Log ==="
tail -n 50 /var/log/gunicorn/access.log

# Check if port is in use
echo "=== Port Check ==="
netstat -tulpn | grep :8000

# Check process
echo "=== Process Check ==="
ps aux | grep gunicorn

# Check permissions
echo "=== Permissions Check ==="
ls -la /opt/driver/
ls -la /var/log/gunicorn/
ls -la /var/run/gunicorn/

# Try to start Gunicorn manually
echo "=== Manual Gunicorn Start ==="
cd /opt/driver
source venv/bin/activate
gunicorn -c gunicorn_config.py driver.wsgi:application --log-level debug 