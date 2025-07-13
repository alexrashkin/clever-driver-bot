#!/bin/bash

echo "🔄 Обновление Chat ID на сервере..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /root/clever-driver-bot
    
    echo "📥 Обновляем код..."
    git pull origin main
    
    echo "🛑 Останавливаем бота..."
    pkill -f "python.*run_bot" || echo "Бот не запущен"
    
    echo "⏳ Ждем остановки..."
    sleep 3
    
    echo "🚀 Запускаем бота с новым Chat ID..."
    nohup /root/clever-driver-bot/venv/bin/python run_bot.py > bot.log 2>&1 &
    
    echo "⏳ Ждем запуска..."
    sleep 5
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo "📋 Проверяем логи бота..."
    if [ -f bot.log ]; then
        echo "=== Последние 10 строк лога ==="
        tail -10 bot.log
    fi
    
    echo "✅ Обновление завершено!"
EOF

echo "🎉 Chat ID обновлен на сервере!" 