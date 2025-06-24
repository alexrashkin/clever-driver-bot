#!/bin/bash

# Backup existing config
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak

# Create new nginx.conf
cat > /etc/nginx/nginx.conf << 'EOL'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 2048;
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    gzip on;
    include /etc/nginx/conf.d/*.conf;
}
EOL

# Remove all existing configs
rm -f /etc/nginx/conf.d/*

# Create driver.conf
cat > /etc/nginx/conf.d/driver.conf << 'EOL'
server {
    listen 80 default_server;
    server_name _;

    access_log /var/log/nginx/driver.access.log;
    error_log /var/log/nginx/driver.error.log;

    client_max_body_size 100M;

    location /static/ {
        alias /opt/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOL

# Set permissions
chown -R www-data:www-data /var/log/nginx
chmod -R 755 /var/log/nginx

# Test and restart nginx
nginx -t && systemctl restart nginx 