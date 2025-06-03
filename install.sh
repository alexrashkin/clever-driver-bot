#!/bin/bash

# 🚗 Clever Driver Bot - Автоматическая установка на VPS
# Дата-центр: Rucloud (Россия, Королёв)
# IP: 194.87.236.174

echo "🚗 =========================================="
echo "🚗 CLEVER DRIVER BOT - УСТАНОВКА НА VPS"
echo "🚗 =========================================="

# Определяем IP сервера
VPS_IP="194.87.236.174"
LOCAL_IP="192.168.0.104"

echo "🔄 1. Обновление системы..."
apt update && apt upgrade -y

echo "📦 2. Установка необходимых пакетов..."
apt install -y python3 python3-pip python3-venv git nano curl wget ufw

echo "📁 3. Создание директории проекта..."
mkdir -p /opt/clever-driver-bot
cd /opt/clever-driver-bot

echo "🐍 4. Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

echo "📦 5. Установка Python зависимостей..."
pip install --upgrade pip
pip install python-telegram-bot==20.8 flask httpx geopy requests python-dotenv

echo "🔧 6. Замена IP адресов в файлах..."
# Заменяем локальный IP на IP VPS
sed -i "s/$LOCAL_IP/$VPS_IP/g" *.py

echo "🔧 7. Настройка прав доступа..."
chmod +x telegram_bot_handler.py
chmod +x https_simple_server.py
chmod +x geolocation_bot.py
chmod +x restart_system.py
chmod +x config_vm.py
chmod +x manage.sh

echo "🔥 8. Настройка firewall..."
ufw allow ssh
ufw allow 8443/tcp
ufw --force enable

echo "⚙️ 9. Создание systemd сервисов..."

# Создание сервиса для Telegram бота
cat > /etc/systemd/system/clever-driver-telegram.service << 'EOF'
[Unit]
Description=Clever Driver Bot Telegram Handler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/clever-driver-bot
Environment=PATH=/opt/clever-driver-bot/venv/bin
ExecStart=/opt/clever-driver-bot/venv/bin/python telegram_bot_handler.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Создание сервиса для HTTPS сервера
cat > /etc/systemd/system/clever-driver-https.service << 'EOF'
[Unit]
Description=Clever Driver Bot HTTPS Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/clever-driver-bot
Environment=PATH=/opt/clever-driver-bot/venv/bin
ExecStart=/opt/clever-driver-bot/venv/bin/python https_simple_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 10. Перезагрузка systemd и включение сервисов..."
systemctl daemon-reload
systemctl enable clever-driver-telegram.service
systemctl enable clever-driver-https.service

echo "🚀 11. Запуск сервисов..."
systemctl start clever-driver-telegram.service
systemctl start clever-driver-https.service

echo ""
echo "✅ =========================================="
echo "✅ УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!"
echo "✅ =========================================="
echo ""
echo "🔗 HTTPS сервер: https://$VPS_IP:8443"
echo "🤖 Telegram бот: @Clever_driver_bot"
echo ""
echo "📊 Проверка статуса:"
echo "   ./manage.sh status"
echo ""
echo "📝 Просмотр логов:"
echo "   ./manage.sh logs"
echo ""
echo "🔧 Управление сервисами:"
echo "   ./manage.sh {start|stop|restart|status|logs}"
echo ""

# Проверка статуса
echo "📊 Текущий статус сервисов:"
systemctl is-active clever-driver-telegram.service
systemctl is-active clever-driver-https.service

echo ""
echo "🎉 Готово! Бот запущен и готов к работе!" 