#!/bin/bash

echo "🤖 Проверка Telegram бота..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /opt/driver-bot
    
    echo "🔍 Проверяем процессы бота..."
    ps aux | grep -E "(python.*run_bot|bot)" | grep -v grep
    
    echo "📋 Проверяем логи бота..."
    if [ -f bot.log ]; then
        echo "=== Последние 20 строк лога бота ==="
        tail -20 bot.log
    else
        echo "❌ Файл bot.log не найден"
    fi
    
    echo "🌐 Проверяем подключение к Telegram API..."
    curl -s "https://api.telegram.org/bot$(grep TELEGRAM_TOKEN config/settings.py | cut -d'"' -f2)/getMe" | head -5
    
    echo "📊 Проверяем статус отслеживания..."
    python -c "
import sys
sys.path.append('.')
from bot.database import db
print('Статус отслеживания:', db.get_tracking_status())
"
    
    echo "✅ Проверка завершена!"
EOF

echo "🎯 Диагностика бота завершена!" 