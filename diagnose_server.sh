#!/bin/bash

echo "🔍 ДИАГНОСТИКА СЕРВЕРА"
echo "======================"

echo "1. Проверяем текущие процессы..."
ps aux | grep python | grep -v grep

echo ""
echo "2. Проверяем статус веб-сервера..."
curl -s http://localhost:5000/ || echo "❌ Веб-сервер не отвечает на порту 5000"

echo ""
echo "3. Проверяем логи веб-сервера..."
if [ -f "logs/web.log" ]; then
    echo "📝 Последние 20 строк лога:"
    tail -20 logs/web.log
else
    echo "❌ Файл логов не найден"
fi

echo ""
echo "4. Проверяем логи Flask..."
if [ -f "flask.log" ]; then
    echo "📝 Последние 20 строк Flask лога:"
    tail -20 flask.log
else
    echo "❌ Файл Flask логов не найден"
fi

echo ""
echo "5. Проверяем виртуальное окружение..."
if [ -d "venv" ]; then
    echo "✅ Виртуальное окружение найдено"
    source venv/bin/activate
    python -c "import flask; print('✅ Flask установлен')" || echo "❌ Flask не установлен"
else
    echo "❌ Виртуальное окружение не найдено"
fi

echo ""
echo "6. Проверяем файл app.py..."
if [ -f "web/app.py" ]; then
    echo "✅ app.py найден"
    python -c "from web.app import app; print('✅ app.py импортируется')" || echo "❌ Ошибка импорта app.py"
else
    echo "❌ app.py не найден"
fi

echo ""
echo "7. Проверяем порты..."
netstat -tlnp | grep :5000 || echo "❌ Порт 5000 не занят"

echo ""
echo "8. Пробуем запустить веб-сервер..."
cd web
python -c "from app import app; print('✅ Приложение готово к запуску')" || echo "❌ Ошибка подготовки приложения" 