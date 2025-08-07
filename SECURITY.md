# Руководство по безопасности

## Текущие меры безопасности

### ✅ Реализованные меры

1. **Аутентификация и авторизация**
   - Хеширование паролей с солью (PBKDF2)
   - Ролевая система (admin, driver, recipient)
   - Сессии с секретным ключом
   - CSRF защита для всех форм

2. **Защита от атак**
   - XSS-защита (паттерны и санитизация)
   - SQL-инъекции (паттерны и проверки)
   - Командные инъекции
   - Проверка User-Agent

3. **Rate Limiting**
   - Ограничение скорости запросов (100 запросов/минуту)
   - Ограничение попыток входа (5 попыток/5 минут)
   - Блокировка IP после 10 неудачных попыток

4. **Безопасность HTTP**
   - CSP заголовки
   - Безопасные заголовки
   - HTTPS принудительно (если настроено)

5. **Логирование**
   - Отдельный файл для событий безопасности
   - Детальное логирование всех атак
   - Логирование IP адресов

## 🔒 Дополнительные рекомендации

### 1. Настройка HTTPS

```bash
# Установка SSL сертификата (Let's Encrypt)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Включение принудительного HTTPS
export FORCE_HTTPS=True
```

### 2. Настройка файрвола

```bash
# Установка UFW
sudo apt-get install ufw

# Настройка правил
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Настройка базы данных

```sql
-- Создание отдельного пользователя для приложения
CREATE USER 'driver_app'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON driver.* TO 'driver_app'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Мониторинг безопасности

```bash
# Установка fail2ban
sudo apt-get install fail2ban

# Настройка /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[flask]
enabled = true
port = http,https
filter = flask
logpath = /path/to/your/app.log
maxretry = 5
bantime = 3600
```

### 5. Резервное копирование

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_FILE="driver.db"

# Создание резервной копии базы данных
sqlite3 $DB_FILE ".backup $BACKUP_DIR/driver_$DATE.db"

# Сжатие резервной копии
gzip $BACKUP_DIR/driver_$DATE.db

# Удаление старых резервных копий (старше 30 дней)
find $BACKUP_DIR -name "driver_*.db.gz" -mtime +30 -delete
```

### 6. Обновления безопасности

```bash
# Автоматические обновления безопасности
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 7. Мониторинг логов

```bash
# Установка logwatch
sudo apt-get install logwatch

# Настройка ежедневных отчетов
sudo nano /etc/cron.daily/00logwatch
```

### 8. Проверка безопасности

```bash
# Установка инструментов безопасности
sudo apt-get install lynis chkrootkit rkhunter

# Запуск проверок
sudo lynis audit system
sudo chkrootkit
sudo rkhunter --check
```

## 🚨 Реагирование на инциденты

### 1. Обнаружение атаки

1. Проверить логи безопасности: `tail -f security.log`
2. Проверить заблокированные IP: `grep "BLOCKED" security.log`
3. Анализ попыток входа: `grep "LOGIN" app.log`

### 2. Блокировка атакующего

```bash
# Ручная блокировка IP
sudo iptables -A INPUT -s ATTACKER_IP -j DROP

# Проверка заблокированных IP
sudo iptables -L INPUT -n --line-numbers
```

### 3. Уведомление администратора

```python
# В web/security.py добавить отправку уведомлений
def send_security_alert(message):
    # Отправка через Telegram бота
    bot_token = config.TELEGRAM_BOT_TOKEN
    admin_chat_id = "YOUR_ADMIN_CHAT_ID"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": admin_chat_id,
        "text": f"🚨 СИГНАЛИЗАЦИЯ БЕЗОПАСНОСТИ\n{message}",
        "parse_mode": "HTML"
    }
    
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")
```

## 📊 Мониторинг и аналитика

### 1. Метрики безопасности

- Количество заблокированных IP
- Количество попыток XSS/SQL инъекций
- Количество неудачных попыток входа
- Время отклика системы

### 2. Дашборд безопасности

```python
@app.route('/admin/security')
@security_check
def security_dashboard():
    """Дашборд безопасности для администраторов"""
    # Статистика атак
    attacks_stats = {
        'xss_attempts': count_xss_attempts(),
        'sql_injection_attempts': count_sql_attempts(),
        'blocked_ips': count_blocked_ips(),
        'failed_logins': count_failed_logins()
    }
    
    return render_template('security_dashboard.html', stats=attacks_stats)
```

## 🔄 Регулярные проверки

### Еженедельно:
- [ ] Проверка логов безопасности
- [ ] Обновление системы
- [ ] Проверка резервных копий
- [ ] Анализ попыток атак

### Ежемесячно:
- [ ] Аудит безопасности
- [ ] Обновление паролей
- [ ] Проверка прав доступа
- [ ] Тестирование восстановления

### Ежеквартально:
- [ ] Полный аудит безопасности
- [ ] Обновление политик безопасности
- [ ] Обучение персонала
- [ ] Тестирование на проникновение

## 📞 Контакты для экстренных случаев

- **Администратор системы**: admin@yourdomain.com
- **Техническая поддержка**: support@yourdomain.com
- **Безопасность**: security@yourdomain.com

## 📚 Полезные ресурсы

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Flask Security Documentation](https://flask-security.readthedocs.io/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
