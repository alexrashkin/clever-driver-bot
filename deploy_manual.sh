#!/bin/bash

echo "🚀 Ручное развертывание Driver Bot на сервере..."

# Обновление системы
echo "📦 Обновление системы..."
sudo apt-get update
sudo apt-get upgrade -y

# Установка Python и pip
echo "🐍 Установка Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# Установка nginx
echo "🌐 Установка Nginx..."
sudo apt-get install -y nginx

# Создание пользователя для приложения
echo "👤 Создание пользователя..."
sudo useradd -m -s /bin/bash driverbot || true
sudo usermod -aG sudo driverbot

# Создание директории приложения
echo "📁 Создание директорий..."
sudo mkdir -p /opt/driver-bot
sudo chown driverbot:driverbot /opt/driver-bot

# Копирование файлов
echo "📋 Копирование файлов..."
sudo cp -r . /opt/driver-bot/
sudo chown -R driverbot:driverbot /opt/driver-bot

# Создание виртуального окружения
echo "🔧 Настройка Python окружения..."
cd /opt/driver-bot
sudo -u driverbot python3 -m venv venv
sudo -u driverbot ./venv/bin/pip install -r requirements.txt

# Создание systemd сервиса
echo "⚙️ Создание systemd сервиса..."
sudo tee /etc/systemd/system/driver-bot.service > /dev/null <<EOF
[Unit]
Description=Driver Bot Web Interface
After=network.target

[Service]
Type=simple
User=driverbot
WorkingDirectory=/opt/driver-bot
Environment=PATH=/opt/driver-bot/venv/bin
ExecStart=/opt/driver-bot/venv/bin/python web_simple.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Настройка Nginx
echo "🌐 Настройка Nginx..."
sudo tee /etc/nginx/sites-available/driver-bot > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /opt/driver-bot/static/;
    }
}
EOF

# Активация сайта
sudo ln -sf /etc/nginx/sites-available/driver-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Перезапуск сервисов
echo "🔄 Перезапуск сервисов..."
sudo systemctl daemon-reload
sudo systemctl enable driver-bot
sudo systemctl start driver-bot
sudo systemctl restart nginx

# Настройка firewall
echo "🔥 Настройка firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

# Проверка статуса
echo "⏳ Проверка статуса..."
sleep 5

echo "📊 Статус сервисов:"
sudo systemctl status driver-bot --no-pager -l
sudo systemctl status nginx --no-pager -l

echo ""
echo "✅ Развертывание завершено!"
echo "🌐 Веб-интерфейс доступен по адресу: http://YOUR_SERVER_IP"
echo "📱 Мобильная страница: http://YOUR_SERVER_IP/mobile_tracker.html"
echo ""
echo "📝 Полезные команды:"
echo "  sudo systemctl status driver-bot    # Статус приложения"
echo "  sudo systemctl restart driver-bot   # Перезапуск приложения"
echo "  sudo journalctl -u driver-bot -f    # Логи приложения"
echo "  sudo systemctl restart nginx        # Перезапуск Nginx" 