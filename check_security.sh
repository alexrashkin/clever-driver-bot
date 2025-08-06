#!/bin/bash

# Скрипт мониторинга безопасности для проекта "Умный водитель"
# Запускается каждые 5 минут через crontab

LOG_FILE="security_monitor.log"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_LOG="$PROJECT_DIR/driver-bot.log"
DB_FILE="$PROJECT_DIR/driver.db"

echo "$(date): Запуск проверки безопасности" >> "$PROJECT_DIR/$LOG_FILE"

# 1. Проверка на подозрительную активность в логах
if [ -f "$MAIN_LOG" ]; then
    SUSPICIOUS_ACTIVITY=$(tail -50 "$MAIN_LOG" | grep -i "security\|attack\|xss\|jstag\|eval\|document.write" | tail -5)
    if [ ! -z "$SUSPICIOUS_ACTIVITY" ]; then
        echo "$(date): ОБНАРУЖЕНА ПОДОЗРИТЕЛЬНАЯ АКТИВНОСТЬ В ЛОГАХ:" >> "$PROJECT_DIR/$LOG_FILE"
        echo "$SUSPICIOUS_ACTIVITY" >> "$PROJECT_DIR/$LOG_FILE"
        
        # Отправка уведомления администратору (если настроен Telegram бот)
        # curl -s "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage" \
        #     -d "chat_id=YOUR_CHAT_ID" \
        #     -d "text=🚨 Обнаружена подозрительная активность на сайте! Проверьте логи."
    fi
fi

# 2. Проверка целостности критических файлов
THEME_MANAGER="$PROJECT_DIR/web/static/theme-manager.js"
if [ -f "$THEME_MANAGER" ]; then
    EXPECTED_MD5="dfb5c552eae48883df961ea3daa6085c"
    ACTUAL_MD5=$(md5sum "$THEME_MANAGER" | cut -d' ' -f1)
    
    if [ "$EXPECTED_MD5" != "$ACTUAL_MD5" ]; then
        echo "$(date): ВНИМАНИЕ! Файл theme-manager.js изменен!" >> "$PROJECT_DIR/$LOG_FILE"
        echo "$(date): Ожидаемый MD5: $EXPECTED_MD5" >> "$PROJECT_DIR/$LOG_FILE"
        echo "$(date): Фактический MD5: $ACTUAL_MD5" >> "$PROJECT_DIR/$LOG_FILE"
    fi
fi

# 3. Проверка базы данных на подозрительные записи
if [ -f "$DB_FILE" ]; then
    SUSPICIOUS_USERS=$(sqlite3 "$DB_FILE" "SELECT id, username, first_name, last_name FROM users WHERE username LIKE '%script%' OR first_name LIKE '%script%' OR last_name LIKE '%script%' OR username LIKE '%eval%' OR first_name LIKE '%eval%' OR last_name LIKE '%eval%';" 2>/dev/null)
    
    if [ ! -z "$SUSPICIOUS_USERS" ]; then
        echo "$(date): ОБНАРУЖЕНЫ ПОДОЗРИТЕЛЬНЫЕ ПОЛЬЗОВАТЕЛИ В БАЗЕ ДАННЫХ:" >> "$PROJECT_DIR/$LOG_FILE"
        echo "$SUSPICIOUS_USERS" >> "$PROJECT_DIR/$LOG_FILE"
    fi
fi

# 4. Проверка на измененные файлы
MODIFIED_FILES=$(find "$PROJECT_DIR" -name "*.js" -o -name "*.html" -o -name "*.py" | xargs grep -l "script\|eval\|document.write\|JSTAG" 2>/dev/null | head -5)

if [ ! -z "$MODIFIED_FILES" ]; then
    echo "$(date): ОБНАРУЖЕНЫ ФАЙЛЫ С ПОДОЗРИТЕЛЬНЫМ КОДОМ:" >> "$PROJECT_DIR/$LOG_FILE"
    echo "$MODIFIED_FILES" >> "$PROJECT_DIR/$LOG_FILE"
fi

# 5. Проверка процессов
PYTHON_PROCESSES=$(ps aux | grep python | grep -v grep | wc -l)
if [ "$PYTHON_PROCESSES" -gt 10 ]; then
    echo "$(date): ВНИМАНИЕ! Обнаружено много Python процессов: $PYTHON_PROCESSES" >> "$PROJECT_DIR/$LOG_FILE"
fi

# 6. Проверка сетевых соединений
NETWORK_CONNECTIONS=$(netstat -tuln | grep :5000 | wc -l)
if [ "$NETWORK_CONNECTIONS" -gt 50 ]; then
    echo "$(date): ВНИМАНИЕ! Много сетевых соединений на порту 5000: $NETWORK_CONNECTIONS" >> "$PROJECT_DIR/$LOG_FILE"
fi

# 7. Проверка размера логов
LOG_SIZE=$(du -m "$MAIN_LOG" 2>/dev/null | cut -f1)
if [ "$LOG_SIZE" -gt 100 ]; then
    echo "$(date): ВНИМАНИЕ! Лог файл слишком большой: ${LOG_SIZE}MB" >> "$PROJECT_DIR/$LOG_FILE"
fi

# 8. Очистка старых записей мониторинга (оставляем последние 1000 строк)
if [ -f "$PROJECT_DIR/$LOG_FILE" ]; then
    tail -1000 "$PROJECT_DIR/$LOG_FILE" > "$PROJECT_DIR/${LOG_FILE}.tmp" && mv "$PROJECT_DIR/${LOG_FILE}.tmp" "$PROJECT_DIR/$LOG_FILE"
fi

echo "$(date): Проверка безопасности завершена" >> "$PROJECT_DIR/$LOG_FILE" 