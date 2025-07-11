# 🚀 Быстрое развертывание Driver Bot

## Вариант 1: Один скрипт (Рекомендуется)

```bash
# 1. Подключитесь к серверу
ssh user@your-server-ip

# 2. Клонируйте репозиторий
git clone https://github.com/alexrashkin/clever-driver-bot.git
cd clever-driver-bot

# 3. Запустите развертывание
chmod +x quick_deploy.sh
./quick_deploy.sh
```

## Вариант 2: Docker

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/alexrashkin/clever-driver-bot.git
cd clever-driver-bot

# 2. Запустите с Docker
chmod +x deploy_server.sh
./deploy_server.sh
```

## Вариант 3: Ручное развертывание

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/alexrashkin/clever-driver-bot.git
cd clever-driver-bot

# 2. Запустите ручное развертывание
chmod +x deploy_manual.sh
./deploy_manual.sh
```

## 🔧 Настройка после развертывания

1. **Настройте Telegram бота**:
   - Откройте файл `web_simple.py`
   - Замените `YOUR_BOT_TOKEN` на ваш токен
   - Замените `TELEGRAM_CHAT_ID` на ID вашего чата

2. **Настройте координаты работы**:
   - Откройте файл `web_simple.py`
   - Измените `WORK_LATITUDE`, `WORK_LONGITUDE`, `WORK_RADIUS`

3. **Перезапустите сервис**:
   ```bash
   # Docker
   docker-compose restart
   
   # Ручное развертывание
   sudo systemctl restart driver-bot
   ```

## 🌐 Доступ к приложению

После развертывания приложение будет доступно:
- **Веб-интерфейс**: `http://YOUR_SERVER_IP`
- **Мобильная страница**: `http://YOUR_SERVER_IP/mobile_tracker.html`

## 📝 Полезные команды

```bash
# Статус сервиса
sudo systemctl status driver-bot

# Логи приложения
sudo journalctl -u driver-bot -f

# Перезапуск
sudo systemctl restart driver-bot

# Остановка
sudo systemctl stop driver-bot

# Запуск
sudo systemctl start driver-bot
```

## 🔍 Устранение неполадок

### Проблемы с доступом
```bash
# Проверка портов
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :5000

# Проверка firewall
sudo ufw status
```

### Проблемы с Nginx
```bash
# Проверка конфигурации
sudo nginx -t

# Перезапуск
sudo systemctl restart nginx

# Логи
sudo tail -f /var/log/nginx/error.log
```

### Проблемы с приложением
```bash
# Проверка логов
sudo journalctl -u driver-bot -f

# Проверка прав доступа
ls -la /opt/driver-bot/
```

## 📞 Поддержка

- 📖 **Подробная документация**: [DEPLOYMENT.md](DEPLOYMENT.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/alexrashkin/clever-driver-bot/issues)
- 💬 **Telegram**: [@alexrashkin](https://t.me/alexrashkin) 