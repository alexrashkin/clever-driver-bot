#!/bin/bash

# Create systemd service
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

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd and restart service
systemctl daemon-reload
systemctl restart driver
systemctl status driver 