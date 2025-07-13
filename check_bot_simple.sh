#!/bin/bash

echo "🤖 Простая проверка бота на сервере..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /root/clever-driver-bot
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo "📋 Проверяем логи бота..."
    if [ -f bot.log ]; then
        echo "=== Последние 5 строк лога ==="
        tail -5 bot.log
    else
        echo "❌ Файл bot.log не найден"
    fi
    
    echo "🌐 Тестируем Telegram API с сервера..."
    python debug_telegram.py
    
    echo "✅ Проверка завершена!"
EOF

echo "🎯 Диагностика завершена!" 