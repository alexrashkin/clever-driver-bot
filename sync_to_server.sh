#!/bin/bash
echo "📤 СИНХРОНИЗАЦИЯ ФАЙЛОВ С СЕРВЕРОМ"
echo "===================================="

echo "📋 Отправка обновленного шаблона..."
scp web/templates/index.html root@194.87.236.174:/root/clever-driver-bot/web/templates/

echo "🔄 Перезапуск Flask..."
ssh root@194.87.236.174 "cd /root/clever-driver-bot && pkill -f 'python.*run_web.py' && sleep 2 && nohup python run_web.py > flask.log 2>&1 &"

echo "✅ Синхронизация завершена!" 