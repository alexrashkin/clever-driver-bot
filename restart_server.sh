#!/bin/bash

echo "🔄 Перезапуск сервера..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /opt/driver-bot
    
    echo "📥 Обновляем код..."
    git pull origin main
    
    echo "🛑 Останавливаем Flask..."
    pkill -f "python.*run_web.py" || echo "Flask не запущен"
    
    echo "⏳ Ждем остановки..."
    sleep 2
    
    echo "🚀 Запускаем Flask..."
    nohup python run_web.py > web.log 2>&1 &
    
    echo "⏳ Ждем запуска..."
    sleep 3
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo "✅ Перезапуск завершен!"
EOF

echo "🎉 Сервер перезапущен!" 