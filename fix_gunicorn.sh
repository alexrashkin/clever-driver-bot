#!/bin/bash

# Create gunicorn config
cat > /opt/driver/gunicorn_config.py << 'EOL'
bind = "127.0.0.1:8000"
workers = 4
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
capture_output = True
daemon = False
pidfile = "/var/run/gunicorn/gunicorn.pid"
max_requests = 1000
max_requests_jitter = 50
EOL

# Create log directories
mkdir -p /var/log/gunicorn
mkdir -p /var/run/gunicorn

# Set permissions
chown -R root:root /var/log/gunicorn
chown -R root:root /var/run/gunicorn
chmod -R 755 /var/log/gunicorn
chmod -R 755 /var/run/gunicorn

# Update service file
cat > /etc/systemd/system/driver.service << 'EOL'
[Unit]
Description=Driver API Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/driver
Environment="PATH=/opt/driver/venv/bin"
ExecStart=/opt/driver/venv/bin/gunicorn -c gunicorn_config.py driver.wsgi:application
Restart=always
RestartSec=5
StandardOutput=append:/var/log/gunicorn/access.log
StandardError=append:/var/log/gunicorn/error.log

[Install]
WantedBy=multi-user.target
EOL

# Reload and restart
systemctl daemon-reload
systemctl restart driver

# Check logs
echo "=== Gunicorn Error Log ==="
cat /var/log/gunicorn/error.log
echo "=== Gunicorn Access Log ==="
cat /var/log/gunicorn/access.log
echo "=== Service Status ==="
systemctl status driver 