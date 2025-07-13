#!/bin/bash

echo "📋 Проверка логов веб-сервера..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /root/clever-driver-bot
    
    echo "📋 Проверяем логи веб-сервера..."
    if [ -f web.log ]; then
        echo "=== Последние 20 строк лога веб-сервера ==="
        tail -20 web.log
    else
        echo "❌ Файл web.log не найден"
    fi
    
    echo "📋 Проверяем логи бота..."
    if [ -f bot.log ]; then
        echo "=== Последние 10 строк лога бота ==="
        tail -10 bot.log
    else
        echo "❌ Файл bot.log не найден"
    fi
    
    echo "✅ Проверка завершена!"
EOF

echo "🎯 Диагностика завершена!" 