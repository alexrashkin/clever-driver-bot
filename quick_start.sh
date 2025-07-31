#!/bin/bash

echo "⚡ Быстрый запуск Flask для диагностики"

# Остановка старых процессов
pkill -f "python.*app.py" 2>/dev/null
sleep 2

# Переход в директорию
cd ~/clever-driver-bot/web

# Активация venv
source ../venv/bin/activate

# Проверка импорта
echo "🔍 Проверка импорта..."
python -c "from app import app; print('✅ Импорт OK')" || {
    echo "❌ Ошибка импорта!"
    exit 1
}

# Запуск в интерактивном режиме (без nohup для диагностики)
echo "🚀 Запуск Flask в интерактивном режиме..."
echo "💡 Если есть ошибки - увидите их в консоли"
echo "💡 Для остановки: Ctrl+C"
echo "🌐 После запуска проверьте: https://cleverdriver.ru/"
echo ""

python app.py 