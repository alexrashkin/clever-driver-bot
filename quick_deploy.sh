#!/bin/bash

echo "🚀 Быстрое развертывание Driver Bot на VPS..."

# Проверка на Ubuntu/Debian
if ! command -v apt-get &> /dev/null; then
    echo "❌ Этот скрипт работает только на Ubuntu/Debian"
    exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
sudo apt-get update
sudo apt-get upgrade -y

# Установка зависимостей
echo "🐍 Установка Python и зависимостей..."
sudo apt-get install -y python3 python3-pip python3-venv nginx git

# Создание директории
echo "📁 Создание директории приложения..."
sudo mkdir -p /opt/driver-bot
sudo chown $USER:$USER /opt/driver-bot

# Копирование файлов
echo "📋 Копирование файлов..."
cp -r . /opt/driver-bot/
cd /opt/driver-bot

# Создание виртуального окружения
echo "🔧 Настройка Python окружения..."
python3 -m venv venv
source venv/bin/pip install -r requirements.txt

# Создание systemd сервиса
echo "⚙️ Создание systemd сервиса..."
sudo tee /etc/systemd/system/driver-bot.service > /dev/null <<EOF
[Unit]
Description=Driver Bot Web Interface
After=network.target

[Service]
Type=simple
User=$USER
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

# Активация сервисов
echo "🔄 Активация сервисов..."
sudo ln -sf /etc/nginx/sites-available/driver-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl daemon-reload
sudo systemctl enable driver-bot
sudo systemctl start driver-bot
sudo systemctl restart nginx

# Настройка firewall
echo "🔥 Настройка firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

# Получение IP адреса
SERVER_IP=$(curl -s ifconfig.me)

echo ""
echo "✅ Развертывание завершено!"
echo "🌐 Веб-интерфейс: http://$SERVER_IP"
echo "📱 Мобильная страница: http://$SERVER_IP/mobile_tracker.html"
echo ""
echo "📝 Полезные команды:"
echo "  sudo systemctl status driver-bot    # Статус приложения"
echo "  sudo systemctl restart driver-bot   # Перезапуск приложения"
echo "  sudo journalctl -u driver-bot -f    # Логи приложения"
echo "  sudo systemctl restart nginx        # Перезапуск Nginx"
echo ""
echo "🔧 Не забудьте настроить Telegram бота в файле web_simple.py!" 