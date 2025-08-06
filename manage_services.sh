#!/bin/bash

echo "🔧 УПРАВЛЕНИЕ СЕРВИСАМИ DRIVER-BOT"
echo "=================================="

case "$1" in
    status)
        echo "📊 Статус сервисов:"
        echo ""
        echo "🤖 Бот:"
        systemctl status driver-bot --no-pager
        echo ""
        echo "🌐 Веб-приложение:"
        systemctl status driver-web --no-pager 2>/dev/null || echo "❌ Сервис driver-web не найден"
        ;;
        
    start)
        echo "🚀 Запуск сервисов..."
        
        # Запускаем бота
        echo "🤖 Запускаем бота..."
        systemctl start driver-bot
        systemctl enable driver-bot
        
        # Проверяем, есть ли сервис для веб-приложения
        if [ -f "/etc/systemd/system/driver-web.service" ]; then
            echo "🌐 Запускаем веб-приложение..."
            systemctl start driver-web
            systemctl enable driver-web
        else
            echo "⚠️ Сервис driver-web не найден. Создаем..."
            cp driver-web.service /etc/systemd/system/
            systemctl daemon-reload
            systemctl start driver-web
            systemctl enable driver-web
        fi
        
        echo "✅ Сервисы запущены!"
        ;;
        
    stop)
        echo "⏹️ Остановка сервисов..."
        
        systemctl stop driver-bot
        systemctl stop driver-web 2>/dev/null || echo "Сервис driver-web не найден"
        
        echo "✅ Сервисы остановлены!"
        ;;
        
    restart)
        echo "🔄 Перезапуск сервисов..."
        
        systemctl restart driver-bot
        systemctl restart driver-web 2>/dev/null || echo "Сервис driver-web не найден"
        
        echo "✅ Сервисы перезапущены!"
        ;;
        
    logs)
        echo "📝 Логи сервисов:"
        echo ""
        echo "🤖 Логи бота:"
        journalctl -u driver-bot -n 20 --no-pager
        echo ""
        echo "🌐 Логи веб-приложения:"
        journalctl -u driver-web -n 20 --no-pager 2>/dev/null || echo "❌ Логи веб-приложения не найдены"
        ;;
        
    install)
        echo "📦 Установка сервисов..."
        
        # Копируем файлы сервисов
        cp driver-bot.service /etc/systemd/system/
        cp driver-web.service /etc/systemd/system/
        
        # Перезагружаем systemd
        systemctl daemon-reload
        
        # Включаем автозапуск
        systemctl enable driver-bot
        systemctl enable driver-web
        
        echo "✅ Сервисы установлены и включены!"
        ;;
        
    *)
        echo "Использование: $0 {status|start|stop|restart|logs|install}"
        echo ""
        echo "Команды:"
        echo "  status   - показать статус сервисов"
        echo "  start    - запустить сервисы"
        echo "  stop     - остановить сервисы"
        echo "  restart  - перезапустить сервисы"
        echo "  logs     - показать логи"
        echo "  install  - установить сервисы"
        exit 1
        ;;
esac 