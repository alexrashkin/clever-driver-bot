#!/bin/bash
echo "🔄 ПЕРЕЗАПУСК FLASK ПРИЛОЖЕНИЯ"
echo "==============================="

echo "📋 Остановка Flask процессов..."
ssh root@194.87.236.174 "pkill -f 'python.*run_web.py'"

echo "⏳ Ожидание 3 секунды..."
sleep 3

echo "🚀 Запуск Flask приложения..."
ssh root@194.87.236.174 "cd /root/clever-driver-bot && nohup python run_web.py > flask.log 2>&1 &"

echo "✅ Flask перезапущен!"
echo "📋 Проверка процессов:"
ssh root@194.87.236.174 "ps aux | grep python | grep run_web" 