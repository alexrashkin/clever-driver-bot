#!/bin/bash

echo "📋 Проверка логов бота на сервере..."

ssh root@194.87.236.174 << 'EOF'
    echo "📁 Переходим в директорию проекта..."
    cd /root/clever-driver-bot
    
    echo "📋 Проверяем логи бота..."
    if [ -f bot.log ]; then
        echo "=== Последние 20 строк лога бота ==="
        tail -20 bot.log
    else
        echo "❌ Файл bot.log не найден"
    fi
    
    echo ""
    echo "🔍 Проверяем процессы..."
    ps aux | grep python | grep -v grep
    
    echo ""
    echo "📊 Проверяем базу данных..."
    python -c "
import sys
sys.path.append('.')
from bot.database import db
print('Последние записи в базе:')
history = db.get_history(5)
for record in history:
    print(f'ID: {record[0]}, Координаты: {record[1]}, {record[2]}, На работе: {record[4]}, Время: {record[5]}')
"
    
    echo "✅ Проверка завершена!"
EOF

echo "🎯 Диагностика завершена!" 