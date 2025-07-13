#!/bin/bash

echo "🤖 Проверка статуса бота на сервере..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /opt/driver-bot
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo "📋 Проверяем логи бота..."
    if [ -f bot.log ]; then
        echo "=== Последние 10 строк лога бота ==="
        tail -10 bot.log
    else
        echo "❌ Файл bot.log не найден"
    fi
    
    echo "🌐 Тестируем Telegram API..."
    python test_telegram.py
    
    echo "✅ Проверка завершена!"
EOF

echo "🎯 Диагностика завершена!" 