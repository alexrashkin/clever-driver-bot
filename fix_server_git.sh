#!/bin/bash
echo "🔧 ИСПРАВЛЕНИЕ GIT КОНФЛИКТА НА СЕРВЕРЕ"
echo "========================================="

echo "📋 Сохранение текущих изменений..."
ssh root@194.87.236.174 "cd /root/clever-driver-bot && git add web/templates/index.html && git commit -m 'Fix manual notification button to use API'"

echo "📥 Обновление кода из репозитория..."
ssh root@194.87.236.174 "cd /root/clever-driver-bot && git pull"

echo "🔄 Перезапуск Flask..."
ssh root@194.87.236.174 "cd /root/clever-driver-bot && pkill -f 'python.*run_web.py' && sleep 2 && nohup python run_web.py > flask.log 2>&1 &"

echo "✅ Git конфликт исправлен!" 