#!/bin/bash
echo "🚀 ЗАПУСК FLASK С АВТОПЕРЕЗАПУСКОМ"
echo "==================================="

cd /root/clever-driver-bot

while true; do
    echo "🔄 Запуск Flask приложения..."
    python run_web.py
    
    echo "⚠️ Flask остановился. Перезапуск через 5 секунд..."
    sleep 5
done 