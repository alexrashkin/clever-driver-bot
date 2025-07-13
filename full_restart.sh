#!/bin/bash

echo "🔄 Полная перезагрузка сервера..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /opt/driver-bot
    
    echo "📥 Обновляем код..."
    git pull origin main
    
    echo "🔍 Проверяем все Python процессы..."
    ps aux | grep python | grep -v grep
    
    echo "🛑 Останавливаем ВСЕ Python процессы..."
    pkill -f python || echo "Нет процессов для остановки"
    
    echo "⏳ Ждем полной остановки..."
    sleep 5
    
    echo "🧹 Очищаем кэш..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    echo "🚀 Запускаем веб-сервер..."
    nohup python run_web.py > web.log 2>&1 &
    
    echo "🤖 Запускаем бота..."
    nohup python run_bot.py > bot.log 2>&1 &
    
    echo "⏳ Ждем запуска..."
    sleep 5
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo "🌐 Тестируем веб-сервер..."
    curl -s http://localhost:5000/test || echo "Веб-сервер не отвечает"
    
    echo "✅ Перезагрузка завершена!"
EOF

echo "🎉 Сервер перезагружен!" 