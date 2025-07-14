#!/bin/bash
set -e
DOMAIN=cleverdriver.ru
WWW_DOMAIN=www.cleverdriver.ru
NGINX_CONF=/etc/nginx/sites-available/$DOMAIN

# 1. Создаем nginx-конфиг
sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $DOMAIN $WWW_DOMAIN;
    return 301 https://$DOMAIN\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN $WWW_DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 2. Включаем сайт
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/$DOMAIN

# 3. Отключаем дефолтный сайт (если есть)
if [ -e /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi

# 4. Проверяем конфиг и перезапускаем nginx
sudo nginx -t && sudo systemctl reload nginx

# 5. Устанавливаем certbot и получаем SSL
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d $DOMAIN -d $WWW_DOMAIN

# 6. Перезапускаем nginx
sudo systemctl reload nginx

echo "\n✅ Всё готово! Проверьте https://$DOMAIN" 