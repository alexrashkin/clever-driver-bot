#!/bin/bash

echo "🔧 Принудительное обновление сервера..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /opt/driver-bot
    
    echo "📥 Обновляем код..."
    git pull origin main
    
    echo "🔍 Проверяем текущие процессы..."
    ps aux | grep python | grep -v grep
    
    echo "🛑 Принудительно останавливаем все Python процессы..."
    pkill -f "python.*run_web.py" || echo "Веб-сервер не найден"
    pkill -f "python.*run_bot" || echo "Бот не найден"
    
    echo "⏳ Ждем полной остановки..."
    sleep 5
    
    echo "🧹 Очищаем кэш Python..."
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    echo "🚀 Запускаем веб-сервер..."
    nohup python run_web.py > web.log 2>&1 &
    
    echo "🤖 Запускаем бота..."
    nohup python run_bot.py > bot.log 2>&1 &
    
    echo "⏳ Ждем запуска..."
    sleep 5
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo "🌐 Проверяем веб-сервер локально..."
    curl -s http://localhost:5000/test || echo "Веб-сервер не отвечает"
    
    echo "✅ Обновление завершено!"
EOF

echo "🎉 Сервер обновлен!" 