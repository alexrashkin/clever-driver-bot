#!/bin/bash

echo "=== Развертывание Driver Bot на новом сервере ==="

# Обновляем систему
echo "Обновляем систему..."
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
echo "Устанавливаем Python и зависимости..."
apt install -y python3 python3-pip python3-venv git curl wget nginx supervisor

# Создаем директорию для проекта
echo "Создаем директорию для проекта..."
mkdir -p /opt/driver-bot
cd /opt/driver-bot

# Создаем виртуальное окружение
echo "Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip install --upgrade pip
pip install -r requirements_new.txt

# Создаем директории для логов
echo "Создаем директории для логов..."
mkdir -p /var/log/driver-bot
chown -R www-data:www-data /var/log/driver-bot

# Создаем файл конфигурации для systemd
echo "Создаем systemd сервис для бота..."
cat > /etc/systemd/system/driver-bot.service << EOF
[Unit]
Description=Driver Bot Telegram Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/driver-bot
Environment=PATH=/opt/driver-bot/venv/bin
ExecStart=/opt/driver-bot/venv/bin/python run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Создаем файл конфигурации для веб-интерфейса
echo "Создаем systemd сервис для веб-интерфейса..."
cat > /etc/systemd/system/driver-web.service << EOF
[Unit]
Description=Driver Bot Web Interface
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/driver-bot
Environment=PATH=/opt/driver-bot/venv/bin
ExecStart=/opt/driver-bot/venv/bin/python run_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Создаем конфигурацию nginx
echo "Настраиваем nginx..."
cat > /etc/nginx/sites-available/driver-bot << EOF
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
}
EOF

# Активируем сайт nginx
ln -sf /etc/nginx/sites-available/driver-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Перезапускаем nginx
systemctl restart nginx

# Включаем и запускаем сервисы
echo "Запускаем сервисы..."
systemctl daemon-reload
systemctl enable driver-bot
systemctl enable driver-web
systemctl start driver-bot
systemctl start driver-web

# Проверяем статус
echo "Проверяем статус сервисов..."
systemctl status driver-bot --no-pager
systemctl status driver-web --no-pager

echo "=== Развертывание завершено ==="
echo "Веб-интерфейс доступен по адресу: http://$(hostname -I | awk '{print $1}')"
echo "Для просмотра логов используйте:"
echo "  journalctl -u driver-bot -f"
echo "  journalctl -u driver-web -f" 