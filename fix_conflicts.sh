#!/bin/bash

echo "=== АВТОМАТИЧЕСКОЕ РЕШЕНИЕ КОНФЛИКТОВ ==="
echo ""

# Проверяем, есть ли конфликты
if git status --porcelain | grep -q "^UU\|^AA\|^DD"; then
    echo "Найдены конфликты. Начинаем их разрешение..."
    echo ""
    
    # Решаем конфликты в web/app.py
    echo "1. Решаем конфликты в web/app.py..."
    if [ -f "web/app.py" ]; then
        # Удаляем все маркеры конфликтов
        sed -i '/^<<<<<<< HEAD$/,/^=======$/d' web/app.py
        sed -i '/^>>>>>>> /d' web/app.py
        echo "✅ Конфликты в web/app.py разрешены"
    fi
    
    # Решаем конфликты в шаблонах
    echo "2. Решаем конфликты в шаблонах..."
    
    if [ -f "web/templates/admin_users.html" ]; then
        sed -i '/^<<<<<<< HEAD$/,/^=======$/d' web/templates/admin_users.html
        sed -i '/^>>>>>>> /d' web/templates/admin_users.html
        echo "✅ Конфликты в admin_users.html разрешены"
    fi
    
    if [ -f "web/templates/user_location.html" ]; then
        sed -i '/^<<<<<<< HEAD$/,/^=======$/d' web/templates/user_location.html
        sed -i '/^>>>>>>> /d' web/templates/user_location.html
        echo "✅ Конфликты в user_location.html разрешены"
    fi
    
    # Добавляем все изменения
    echo "3. Добавляем изменения в git..."
    git add .
    
    # Фиксируем изменения
    echo "4. Фиксируем изменения..."
    git commit -m "Resolve merge conflicts and preserve security updates"
    
    # Отправляем изменения
    echo "5. Отправляем изменения на сервер..."
    git push
    
    echo ""
    echo "🎉 Все конфликты успешно разрешены!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Перезапустите приложение: ./restart_web_app.sh"
    echo "2. Проверьте логи: tail -f driver-bot.log"
    echo "3. Протестируйте безопасность: откройте /test_security в браузере"
    
else
    echo "Конфликтов не найдено. Все в порядке!"
fi 