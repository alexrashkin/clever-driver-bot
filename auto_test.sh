#!/bin/bash

echo "🧹 Очистка last_checked_id/time..."
rm -f bot/last_checked_id.txt bot/last_checked_time.txt

echo "🤖 Запуск бота (оставьте это окно открытым!)"
cd bot && python main.py &
BOT_PID=$!

echo "⏳ Ждем 5 секунд для запуска бота..."
sleep 5

echo "📊 Запуск тестового перехода..."
cd .. && python test_notifications.py

echo "⏳ Ждем 10 секунд для обработки мониторингом..."
sleep 10

echo "🛑 Останавливаем бота..."
kill $BOT_PID 2>/dev/null

echo "✅ Тест завершен! Проверьте логи выше." 