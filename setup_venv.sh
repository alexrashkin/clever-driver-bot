#!/bin/bash

echo "🔧 Настройка виртуального окружения для Clever_driver_bot..."
echo

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем pip
echo "📦 Обновляем pip..."
python -m pip install --upgrade pip

# Устанавливаем зависимости
echo "📋 Устанавливаем зависимости..."
pip install -r requirements.txt

echo
echo "✅ Виртуальное окружение готово!"
echo
echo "🚀 Теперь можете запустить бота:"
echo "   python web_geolocation_server.py"
echo
echo "📝 Для активации окружения в будущем используйте:"
echo "   source venv/bin/activate" 