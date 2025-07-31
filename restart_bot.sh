#!/bin/bash

echo "🔄 Перезапуск бота на сервере..."

# Останавливаем сервис
echo "⏹️ Останавливаем сервис..."
systemctl stop driver-bot

# Ждем немного
sleep 2

# Проверяем, что процесс остановлен
if pgrep -f "python.*main.py" > /dev/null; then
    echo "🔪 Принудительно завершаем процессы..."
    pkill -9 -f "python.*main.py"
    sleep 1
fi

# Запускаем сервис
echo "▶️ Запускаем сервис..."
systemctl start driver-bot

# Ждем запуска
sleep 3

# Проверяем статус
echo "📊 Проверяем статус..."
systemctl status driver-bot --no-pager

# Показываем последние логи
echo "📝 Последние логи:"
tail -10 logs/driver-bot.log

echo "✅ Перезапуск завершен!" 