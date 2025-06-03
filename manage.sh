#!/bin/bash

case "$1" in
    start)
        systemctl start clever-driver-telegram.service
        systemctl start clever-driver-https.service
        echo "✅ Сервисы запущены"
        ;;
    stop)
        systemctl stop clever-driver-telegram.service
        systemctl stop clever-driver-https.service
        echo "⏹️ Сервисы остановлены"
        ;;
    restart)
        systemctl restart clever-driver-telegram.service
        systemctl restart clever-driver-https.service
        echo "🔄 Сервисы перезапущены"
        ;;
    status)
        systemctl status clever-driver-telegram.service
        systemctl status clever-driver-https.service
        ;;
    logs)
        journalctl -u clever-driver-telegram.service -u clever-driver-https.service -f
        ;;
    logs-telegram)
        journalctl -u clever-driver-telegram.service -f
        ;;
    logs-https)
        journalctl -u clever-driver-https.service -f
        ;;
    *)
        echo "🚗 Clever Driver Bot - Управление сервисами"
        echo "Использование: $0 {start|stop|restart|status|logs|logs-telegram|logs-https}"
        echo ""
        echo "  start         - Запустить все сервисы"
        echo "  stop          - Остановить все сервисы"  
        echo "  restart       - Перезапустить все сервисы"
        echo "  status        - Показать статус сервисов"
        echo "  logs          - Показать логи всех сервисов"
        echo "  logs-telegram - Показать логи Telegram бота"
        echo "  logs-https    - Показать логи HTTPS сервера"
        exit 1
        ;;
esac 