#!/bin/bash
echo "🔧 ИСПРАВЛЕНИЕ КОНФИГУРАЦИИ NGINX"
echo "===================================="

# Создаем резервную копию
echo "📋 Создание резервной копии..."
ssh root@194.87.236.174 "cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup"

# Создаем новую конфигурацию
echo "📝 Создание новой конфигурации..."
cat > nginx_config_new << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    # Перенаправление на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/194.87.236.174/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/194.87.236.174/privkey.pem;

    # Проксирование всех запросов к Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF

# Копируем конфигурацию на сервер
echo "📤 Копирование конфигурации на сервер..."
scp nginx_config_new root@194.87.236.174:/tmp/nginx_config_new

# Применяем конфигурацию
echo "🔧 Применение новой конфигурации..."
ssh root@194.87.236.174 "mv /tmp/nginx_config_new /etc/nginx/sites-available/default"

# Проверяем синтаксис
echo "✅ Проверка синтаксиса..."
ssh root@194.87.236.174 "nginx -t"

# Перезапускаем nginx
echo "🔄 Перезапуск nginx..."
ssh root@194.87.236.174 "systemctl reload nginx"

echo "✅ Готово! Конфигурация nginx обновлена." 