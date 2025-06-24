#!/bin/bash

echo "=== Развертывание упрощенного Driver Bot ==="

# Обновляем систему
echo "Обновляем систему..."
apt update && apt upgrade -y

# Устанавливаем Python
echo "Устанавливаем Python..."
apt install -y python3 python3-pip python3-venv

# Создаем директорию
echo "Создаем директорию..."
mkdir -p /opt/driver-bot
cd /opt/driver-bot

# Создаем виртуальное окружение
echo "Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip install --upgrade pip
pip install python-telegram-bot

# Создаем systemd сервис
echo "Создаем systemd сервис..."
cat > /etc/systemd/system/driver-bot.service << EOF
[Unit]
Description=Driver Bot Simple
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/driver-bot
Environment=PATH=/opt/driver-bot/venv/bin
ExecStart=/opt/driver-bot/venv/bin/python run_simple_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Включаем и запускаем сервис
echo "Запускаем сервис..."
systemctl daemon-reload
systemctl enable driver-bot
systemctl start driver-bot

# Проверяем статус
echo "Проверяем статус..."
systemctl status driver-bot --no-pager

echo "=== Развертывание завершено ==="
echo "Для просмотра логов: journalctl -u driver-bot -f" 