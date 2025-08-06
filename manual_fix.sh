#!/bin/bash

echo "=== РУЧНОЕ РЕШЕНИЕ КОНФЛИКТОВ ==="
echo ""

# Проверяем статус
echo "1. Проверяем статус git..."
git status

echo ""
echo "2. Удаляем маркеры конфликтов из web/app.py..."
if [ -f "web/app.py" ]; then
    # Удаляем маркеры конфликтов
    sed -i '/^<<<<<<< HEAD$/,/^=======$/d' web/app.py
    sed -i '/^>>>>>>> /d' web/app.py
    echo "✅ Маркеры конфликтов удалены из web/app.py"
fi

echo ""
echo "3. Удаляем маркеры конфликтов из шаблонов..."
if [ -f "web/templates/admin_users.html" ]; then
    sed -i '/^<<<<<<< HEAD$/,/^=======$/d' web/templates/admin_users.html
    sed -i '/^>>>>>>> /d' web/templates/admin_users.html
    echo "✅ Маркеры конфликтов удалены из admin_users.html"
fi

if [ -f "web/templates/user_location.html" ]; then
    sed -i '/^<<<<<<< HEAD$/,/^=======$/d' web/templates/user_location.html
    sed -i '/^>>>>>>> /d' web/templates/user_location.html
    echo "✅ Маркеры конфликтов удалены из user_location.html"
fi

echo ""
echo "4. Добавляем изменения в git..."
git add .

echo ""
echo "5. Фиксируем изменения..."
git commit -m "Resolve merge conflicts and preserve security updates"

echo ""
echo "6. Отправляем изменения..."
git push

echo ""
echo "🎉 Конфликты разрешены!"
echo ""
echo "Следующие шаги:"
echo "1. Перезапустите приложение: ./restart_web_app.sh"
echo "2. Проверьте логи: tail -f driver-bot.log" 