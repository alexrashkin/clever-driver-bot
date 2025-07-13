#!/bin/bash

echo "🔄 Обновление сервера..."

# Подключаемся к серверу и обновляем код
ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /opt/driver-bot
    
    echo "📥 Обновляем код с GitHub..."
    git pull origin main
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep -E "(python|flask)" | grep -v grep
    
    echo "🛑 Останавливаем старые процессы..."
    pkill -f "python.*run_web.py" || echo "Веб-сервер не запущен"
    pkill -f "python.*run_bot" || echo "Бот не запущен"
    
    echo "🚀 Запускаем веб-сервер..."
    nohup python run_web.py > web.log 2>&1 &
    
    echo "🤖 Запускаем бота..."
    nohup python run_bot.py > bot.log 2>&1 &
    
    echo "⏳ Ждем запуска..."
    sleep 3
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep -E "(python|flask)" | grep -v grep
    
    echo "🌐 Проверяем веб-сервер..."
    curl -s http://localhost:5000/ | head -5
    
    echo "✅ Обновление завершено!"
EOF

echo "🎉 Сервер обновлен!" 