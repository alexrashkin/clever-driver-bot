#!/bin/bash

echo "🔧 Перезапуск Умный водитель веб-приложения..."

# Остановка старых процессов
echo "📴 Остановка старых процессов..."
pkill -f "python.*app.py" 2>/dev/null
pkill -f "python.*web" 2>/dev/null

# Ждем 2 секунды
sleep 2

# Переход в рабочую директорию
cd ~/clever-driver-bot/web

# Активация виртуального окружения
echo "🐍 Активация виртуального окружения..."
source ../venv/bin/activate

# Проверка что Flask установлен
python -c "import flask; print('✅ Flask OK')" || {
    echo "❌ Flask не найден! Устанавливаю..."
    pip install flask
}

# Проверка что приложение импортируется
echo "🔍 Проверка приложения..."
python -c "from app import app; print('✅ App imports OK')" || {
    echo "❌ Ошибка импорта приложения!"
    exit 1
}

# Создаем папку для логов если её нет
mkdir -p ../logs

# Запуск приложения в фоне
echo "🚀 Запуск приложения..."
nohup python app.py > ../logs/web.log 2>&1 &

# Получаем PID процесса
WEB_PID=$!

# Ждем 3 секунды и проверяем что процесс запустился
sleep 3

if ps -p $WEB_PID > /dev/null; then
    echo "✅ Веб-приложение запущено! PID: $WEB_PID"
    echo "📊 Лог: tail -f ~/clever-driver-bot/logs/web.log"
    echo "🌐 URL: https://cleverdriver.ru/"
    
    # Проверяем что сервер отвечает
    sleep 2
    if curl -s http://localhost:5000/ > /dev/null; then
        echo "✅ Сервер отвечает на порту 5000"
    else
        echo "⚠️  Сервер не отвечает, проверьте логи"
    fi
    
else
    echo "❌ Ошибка запуска! Проверьте логи:"
    cat ../logs/web.log
    exit 1
fi

echo "🎉 Готово! Теперь доступно:"
echo "  📱 Регистрация: /register"
echo "  🚪 Вход: /login"
echo "  👥 Админка: /admin/users"
echo "  ��️ Трекер: /tracker" 