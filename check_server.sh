#!/bin/bash

echo "🔍 Проверка сервера..."

# Проверяем доступность сайта
echo "🌐 Проверяем главную страницу..."
curl -s -k https://194.87.236.174/ | grep -q "Driver Bot" && echo "✅ Главная страница работает" || echo "❌ Главная страница не работает"

echo "📱 Проверяем мобильный трекер..."
curl -s -k https://194.87.236.174/mobile | grep -q "Driver Tracker" && echo "✅ Мобильный трекер работает" || echo "❌ Мобильный трекер не работает"

echo "🔄 Проверяем маршрут /toggle..."
curl -s -k -X POST https://194.87.236.174/toggle -d "" | grep -q "Not Found" && echo "❌ Маршрут /toggle не работает (404)" || echo "✅ Маршрут /toggle работает"

echo "📊 Проверяем API статуса..."
curl -s -k https://194.87.236.174/api/status | grep -q "success" && echo "✅ API статуса работает" || echo "❌ API статуса не работает"

echo "🎯 Диагностика завершена!" 