#!/bin/bash

# Скрипт настройки самоподписанного SSL для IP-адреса
# Выполнять на сервере с правами root

set -e

echo "🔒 Настройка самоподписанного SSL для IP-адреса..."
echo "================================================"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен выполняться с правами root"
    exit 1
fi

# Остановка сервисов
echo "⏸️ Остановка сервисов..."
systemctl stop nginx
systemctl stop driver-bot

# Создание директории для сертификатов
echo "📁 Создание директории для сертификатов..."
mkdir -p /etc/ssl/driver-bot

# Генерация самоподписанного сертификата
echo "🔐 Генерация самоподписанного сертификата..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/driver-bot/private.key \
    -out /etc/ssl/driver-bot/certificate.crt \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=DriverBot/OU=IT/CN=194.87.236.174" \
    -addext "subjectAltName=IP:194.87.236.174,DNS:194.87.236.174"

# Создание конфигурации Nginx с самоподписанным сертификатом
echo "📝 Создание конфигурации Nginx..."
cat > /etc/nginx/sites-available/driver-bot << 'EOF'
server {
    listen 80;
    server_name 194.87.236.174;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 194.87.236.174;
    
    # SSL Configuration (self-signed)
    ssl_certificate /etc/ssl/driver-bot/certificate.crt;
    ssl_certificate_key /etc/ssl/driver-bot/private.key;
    
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

# Удаление старых конфигураций
echo "🗑️ Очистка старых конфигураций..."
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/driver-bot-*

# Активация новой конфигурации
echo "🔗 Активация конфигурации..."
ln -sf /etc/nginx/sites-available/driver-bot /etc/nginx/sites-enabled/

# Проверка конфигурации
echo "🔍 Проверка конфигурации Nginx..."
nginx -t

# Запуск сервисов
echo "🚀 Запуск сервисов..."
systemctl start nginx
systemctl start driver-bot

# Проверка статуса
echo "📊 Проверка статуса сервисов..."
systemctl status nginx --no-pager -l
systemctl status driver-bot --no-pager -l

echo ""
echo "✅ Самоподписанный SSL настроен!"
echo "🌐 Доступ к приложению: https://194.87.236.174"
echo "⚠️  ВНИМАНИЕ: Браузер покажет предупреждение о самоподписанном сертификате"
echo "   Это нормально для самоподписанных сертификатов"
echo ""
echo "📋 Команды для проверки:"
echo "   curl -k -I https://194.87.236.174"
echo "   systemctl status nginx"
echo "   systemctl status driver-bot"
echo ""
echo "🔧 Для обновления кода с исправлением дублирования:"
echo "   cd /opt/driver-bot && git pull origin main && systemctl restart driver-bot" 