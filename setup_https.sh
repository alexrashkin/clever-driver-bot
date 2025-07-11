#!/bin/bash

# Скрипт настройки HTTPS для Driver Bot
# Выполнять на сервере с правами root

set -e

echo "🔒 Настройка HTTPS для Driver Bot..."
echo "=================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен выполняться с правами root"
    exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Установка Certbot
echo "🔧 Установка Certbot..."
apt install certbot python3-certbot-nginx -y

# Остановка сервисов
echo "⏸️ Остановка сервисов..."
systemctl stop nginx
systemctl stop driver-bot

# Создание временной конфигурации Nginx для получения сертификата
echo "📝 Создание временной конфигурации Nginx..."
cat > /etc/nginx/sites-available/driver-bot-temp << 'EOF'
server {
    listen 80;
    server_name 194.87.236.174.nip.io;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Активация временной конфигурации
ln -sf /etc/nginx/sites-available/driver-bot-temp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
echo "🔍 Проверка конфигурации Nginx..."
nginx -t

# Запуск Nginx
echo "🚀 Запуск Nginx..."
systemctl start nginx

# Получение SSL сертификата
echo "🔐 Получение SSL сертификата..."
certbot --nginx -d 194.87.236.174.nip.io --non-interactive --agree-tos --email admin@example.com

# Замена конфигурации на полную HTTPS версию
echo "📝 Обновление конфигурации Nginx..."
cat > /etc/nginx/sites-available/driver-bot << 'EOF'
server {
    listen 80;
    server_name 194.87.236.174.nip.io;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 194.87.236.174.nip.io;
    
    # SSL Configuration (will be added by Certbot)
    ssl_certificate /etc/letsencrypt/live/194.87.236.174.nip.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/194.87.236.174.nip.io/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to Flask app
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/driver-bot/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Активация новой конфигурации
ln -sf /etc/nginx/sites-available/driver-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/driver-bot-temp

# Проверка конфигурации
echo "🔍 Проверка конфигурации Nginx..."
nginx -t

# Перезапуск сервисов
echo "🔄 Перезапуск сервисов..."
systemctl reload nginx
systemctl start driver-bot

# Настройка автообновления сертификата
echo "⏰ Настройка автообновления сертификата..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Проверка статуса
echo "📊 Проверка статуса сервисов..."
systemctl status nginx --no-pager -l
systemctl status driver-bot --no-pager -l

echo ""
echo "✅ HTTPS настройка завершена!"
echo "🌐 Доступ к приложению: https://194.87.236.174.nip.io"
echo "🔒 SSL сертификат будет автоматически обновляться"
echo ""
echo "📋 Команды для управления:"
echo "   systemctl status nginx"
echo "   systemctl status driver-bot"
echo "   journalctl -u nginx -f"
echo "   journalctl -u driver-bot -f" 