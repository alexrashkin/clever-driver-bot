#!/bin/bash

echo "🛑 Останавливаем бота на сервере..."

# Останавливаем все процессы Python с main.py
ssh root@194.87.236.174 "pkill -f 'python.*main.py'"

# Ждем немного
sleep 2

# Проверяем, что процессы остановлены
echo "📊 Проверяем статус..."
ssh root@194.87.236.174 "ps aux | grep -E '(python.*main.py|bot)' | grep -v grep"

echo "✅ Остановка завершена!" 