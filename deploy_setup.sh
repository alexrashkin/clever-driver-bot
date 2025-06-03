#!/bin/bash

# CLEVER DRIVER BOT - AUTO DEPLOYMENT SCRIPT
# ==========================================

echo "🚗 Clever Driver Bot - Автоматическая установка на ВМ"
echo "======================================================"

# Проверка ОС
if [ -f /etc/debian_version ]; then
    OS="debian"
    echo "✅ Обнаружена Debian/Ubuntu система"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
    echo "✅ Обнаружена RedHat/CentOS система"
else
    echo "❌ Неподдерживаемая ОС"
    exit 1
fi

# Установка зависимостей
echo "📦 Установка системных зависимостей..."
if [ "$OS" = "debian" ]; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv curl wget
elif [ "$OS" = "redhat" ]; then
    sudo yum install -y python3 python3-pip curl wget
fi

# Проверка Python
echo "🐍 Проверка Python..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3 не установлен!"
    exit 1
fi

# Создание директории проекта
echo "📁 Создание директории проекта..."
PROJECT_DIR="/opt/clever-driver-bot"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# Создание виртуального окружения
echo "🔧 Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo "📚 Установка Python пакетов..."
pip install --upgrade pip
pip install flask requests python-telegram-bot geopy httpx

# Создание systemd сервисов
echo "⚙️ Создание systemd сервисов..."

# Telegram Bot Service
sudo tee /etc/systemd/system/clever-telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Clever Driver Bot - Telegram Handler
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python telegram_bot_handler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# HTTPS Server Service
sudo tee /etc/systemd/system/clever-https-server.service > /dev/null <<EOF
[Unit]
Description=Clever Driver Bot - HTTPS Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python https_simple_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Включение сервисов
sudo systemctl daemon-reload
sudo systemctl enable clever-telegram-bot.service
sudo systemctl enable clever-https-server.service

# Настройка файрволла
echo "🔥 Настройка файрволла..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8443/tcp
    echo "✅ UFW: открыт порт 8443"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=8443/tcp
    sudo firewall-cmd --reload
    echo "✅ FirewallD: открыт порт 8443"
fi

# Создание скрипта управления
tee manage.sh > /dev/null <<EOF
#!/bin/bash
# Clever Driver Bot Management Script

case "\$1" in
    start)
        echo "🚀 Запуск Clever Driver Bot..."
        sudo systemctl start clever-telegram-bot.service
        sudo systemctl start clever-https-server.service
        ;;
    stop)
        echo "🛑 Остановка Clever Driver Bot..."
        sudo systemctl stop clever-telegram-bot.service
        sudo systemctl stop clever-https-server.service
        ;;
    restart)
        echo "🔄 Перезапуск Clever Driver Bot..."
        sudo systemctl restart clever-telegram-bot.service
        sudo systemctl restart clever-https-server.service
        ;;
    status)
        echo "📊 Статус Clever Driver Bot:"
        sudo systemctl status clever-telegram-bot.service
        sudo systemctl status clever-https-server.service
        ;;
    logs)
        echo "📋 Логи Clever Driver Bot:"
        sudo journalctl -u clever-telegram-bot.service -f
        ;;
    *)
        echo "Использование: \$0 {start|stop|restart|status|logs}"
        ;;
esac
EOF

chmod +x manage.sh

echo ""
echo "🎉 Установка завершена!"
echo "======================================================"
echo "📂 Проект установлен в: $PROJECT_DIR"
echo "⚙️ Сервисы зарегистрированы в systemd"
echo "🔥 Порт 8443 открыт в файрволле"
echo ""
echo "📋 Команды управления:"
echo "  ./manage.sh start    - запуск"
echo "  ./manage.sh stop     - остановка"
echo "  ./manage.sh restart  - перезапуск"
echo "  ./manage.sh status   - статус"
echo "  ./manage.sh logs     - логи"
echo ""
echo "⚠️ ВАЖНО: Скопируйте файлы проекта в $PROJECT_DIR"
echo "⚠️ И обновите IP адрес в коде под вашу ВМ!"
echo "======================================================" 