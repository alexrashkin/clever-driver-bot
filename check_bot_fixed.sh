#!/bin/bash

echo "🤖 Проверка бота на сервере (исправленная версия)..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /root/clever-driver-bot
    
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo "📋 Проверяем логи бота..."
    if [ -f bot.log ]; then
        echo "=== Последние 15 строк лога бота ==="
        tail -15 bot.log
    else
        echo "❌ Файл bot.log не найден"
    fi
    
    echo "🌐 Тестируем Telegram API..."
    /root/clever-driver-bot/venv/bin/python test_telegram.py
    
    echo "✅ Проверка завершена!"
EOF

echo "🎯 Диагностика завершена!" 