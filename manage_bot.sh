#!/bin/bash

# Скрипт для управления ботом Умный водитель

BOT_SERVICE="driver-bot"
BOT_PROCESS="python.*main.py"
BOT_DIR="/root/clever-driver-bot"

case "$1" in
    start)
        echo "🚀 Запуск бота..."
        
        # Останавливаем сервис если запущен
        systemctl stop $BOT_SERVICE 2>/dev/null
        
        # Убиваем все процессы бота
        pkill -9 -f "$BOT_PROCESS" 2>/dev/null
        
        # Ждем завершения
        sleep 2
        
        # Запускаем сервис
        systemctl start $BOT_SERVICE
        
        # Проверяем статус
        sleep 3
        systemctl status $BOT_SERVICE --no-pager
        
        echo "✅ Бот запущен"
        ;;
        
    stop)
        echo "⏹️ Остановка бота..."
        
        # Останавливаем сервис
        systemctl stop $BOT_SERVICE
        
        # Убиваем все процессы бота
        pkill -9 -f "$BOT_PROCESS" 2>/dev/null
        
        echo "✅ Бот остановлен"
        ;;
        
    restart)
        echo "🔄 Перезапуск бота..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        echo "📊 Статус бота:"
        systemctl status $BOT_SERVICE --no-pager
        
        echo ""
        echo "🔍 Процессы бота:"
        ps aux | grep "$BOT_PROCESS" | grep -v grep
        
        echo ""
        echo "📝 Последние логи:"
        if [ -f "$BOT_DIR/logs/driver-bot.log" ]; then
            tail -10 "$BOT_DIR/logs/driver-bot.log"
        else
            echo "Файл логов не найден"
        fi
        ;;
        
    logs)
        echo "📝 Логи бота:"
        if [ -f "$BOT_DIR/logs/driver-bot.log" ]; then
            tail -f "$BOT_DIR/logs/driver-bot.log"
        else
            echo "Файл логов не найден"
        fi
        ;;
        
    test)
        echo "🧪 Тестирование бота..."
        cd "$BOT_DIR"
        
        # Проверяем, что только один процесс бота запущен
        bot_processes=$(ps aux | grep "$BOT_PROCESS" | grep -v grep | wc -l)
        echo "Процессов бота: $bot_processes"
        
        if [ "$bot_processes" -eq 0 ]; then
            echo "❌ Бот не запущен"
        elif [ "$bot_processes" -eq 1 ]; then
            echo "✅ Бот запущен корректно (1 процесс)"
        else
            echo "⚠️ Запущено несколько процессов бота ($bot_processes)"
            echo "Процессы:"
            ps aux | grep "$BOT_PROCESS" | grep -v grep
        fi
        
        # Тестируем API бота
        echo ""
        echo "📡 Тестирование Telegram API..."
        python3 check_bot_status.py
        ;;
        
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить бота"
        echo "  stop    - Остановить бота"
        echo "  restart - Перезапустить бота"
        echo "  status  - Показать статус и логи"
        echo "  logs    - Показать логи в реальном времени"
        echo "  test    - Протестировать бота"
        exit 1
        ;;
esac 