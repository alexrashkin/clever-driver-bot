#!/bin/bash

# Скрипт настройки HTTP доступа без SSL
# Выполнять на сервере с правами root

set -e

echo "🌐 Настройка HTTP доступа без SSL..."
echo "=================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен выполняться с правами root"
    exit 1
fi

# Остановка сервисов
echo "⏸️ Остановка сервисов..."
systemctl stop nginx
systemctl stop driver-bot

# Создание конфигурации Nginx только для HTTP
echo "📝 Создание конфигурации Nginx для HTTP..."
cat > /etc/nginx/sites-available/driver-bot << 'EOF'
server {
    listen 80;
    server_name 194.87.236.174;
    
    # Security Headers
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
echo "✅ HTTP доступ настроен!"
echo "🌐 Доступ к приложению: http://194.87.236.174"
echo "⚠️  ВНИМАНИЕ: Соединение не защищено SSL"
echo ""
echo "📋 Команды для проверки:"
echo "   curl -I http://194.87.236.174"
echo "   systemctl status nginx"
echo "   systemctl status driver-bot"
echo ""
echo "🔧 Для обновления кода с исправлением дублирования:"
echo "   cd /opt/driver-bot && git pull origin main && systemctl restart driver-bot" 