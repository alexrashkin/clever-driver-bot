@echo off
echo 🔧 Настройка виртуального окружения для Clever_driver_bot...
echo.

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat

REM Обновляем pip
echo 📦 Обновляем pip...
python -m pip install --upgrade pip

REM Устанавливаем зависимости
echo 📋 Устанавливаем зависимости...
pip install -r requirements.txt

echo.
echo ✅ Виртуальное окружение готово!
echo.
echo 🚀 Теперь можете запустить бота:
echo    python web_geolocation_server.py
echo.
echo 📝 Для активации окружения в будущем используйте:
echo    venv\Scripts\activate
echo.
pause 