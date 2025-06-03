# 🚗 Clever Driver Bot

Система автоматического уведомления о прибытии/отъезде через Telegram с геолокацией.

## 📋 Описание

Clever Driver Bot - это система, которая отслеживает ваше местоположение и автоматически отправляет уведомления в Telegram когда вы прибываете домой или покидаете дом.

### ✨ Возможности
- 📍 Автоматическое отслеживание геолокации
- 📱 Уведомления в Telegram при прибытии/отъезде
- 🔒 HTTPS веб-интерфейс для iOS/Android
- 🧪 Тестовые уведомления
- ⚙️ Автоматический запуск как системный сервис

## 🖥️ VPS Сервер

**Дата-центр**: Rucloud (Россия, Королёв)  
**IP**: 194.87.236.174  
**OS**: Debian 12 (ENG)  
**Конфигурация**: 1x2.2ГГц, 2Гб RAM, 20Гб HDD  

## 🚀 Быстрая установка на VPS

### Автоматическая установка (рекомендуется)

```bash
# 1. Подключение к серверу
ssh root@194.87.236.174

# 2. Клонирование репозитория
git clone https://github.com/YOUR_USERNAME/clever-driver-bot.git /opt/clever-driver-bot

# 3. Переход в директорию
cd /opt/clever-driver-bot

# 4. Запуск автоматической установки
chmod +x install.sh
./install.sh
```

### Ручная установка

```bash
# 1. Обновление системы
apt update && apt upgrade -y

# 2. Установка зависимостей
apt install -y python3 python3-pip python3-venv git ufw

# 3. Клонирование проекта
git clone https://github.com/YOUR_USERNAME/clever-driver-bot.git /opt/clever-driver-bot
cd /opt/clever-driver-bot

# 4. Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# 5. Установка Python пакетов
pip install -r requirements.txt

# 6. Настройка IP адресов
sed -i 's/192.168.0.104/194.87.236.174/g' *.py

# 7. Настройка firewall
ufw allow ssh
ufw allow 8443/tcp
ufw enable

# 8. Создание systemd сервисов (см. install.sh)

# 9. Запуск
systemctl start clever-driver-telegram.service
systemctl start clever-driver-https.service
```

## 🎛️ Управление сервисами

```bash
# Запуск всех сервисов
./manage.sh start

# Остановка всех сервисов
./manage.sh stop

# Перезапуск всех сервисов
./manage.sh restart

# Проверка статуса
./manage.sh status

# Просмотр логов
./manage.sh logs

# Логи только Telegram бота
./manage.sh logs-telegram

# Логи только HTTPS сервера
./manage.sh logs-https
```

## 🔗 Доступ

После установки система будет доступна по адресам:

- **HTTPS сервер**: https://194.87.236.174:8443
- **Telegram бот**: @Clever_driver_bot

## 📱 Настройка телефона

### iPhone (Safari)
1. Откройте Safari
2. Перейдите на https://194.87.236.174:8443
3. Нажмите "Дополнительно" → "Перейти на сайт"
4. Разрешите доступ к геолокации
5. Используйте кнопки для тестирования

### Android (Chrome)
1. Откройте Chrome
2. Перейдите на https://194.87.236.174:8443
3. Разрешите доступ к геолокации
4. Используйте кнопки для тестирования

## ⚙️ Конфигурация

### Основные файлы
- `telegram_bot_handler.py` - Telegram бот
- `https_simple_server.py` - HTTPS веб-сервер
- `geolocation_bot.py` - Логика геолокации
- `geo_locations.json` - Координаты дома
- `requirements.txt` - Python зависимости

### Настройка местоположения дома
Отредактируйте файл `geo_locations.json`:
```json
{
  "locations": [
    {
      "name": "Дом",
      "latitude": 55.676803,
      "longitude": 37.523510,
      "radius": 50
    }
  ]
}
```

## 🔧 Troubleshooting

### Проверка статуса сервисов
```bash
systemctl status clever-driver-telegram.service
systemctl status clever-driver-https.service
```

### Просмотр логов
```bash
journalctl -u clever-driver-telegram.service -f
journalctl -u clever-driver-https.service -f
```

### Перезапуск при проблемах
```bash
systemctl restart clever-driver-telegram.service
systemctl restart clever-driver-https.service
```

### Проверка портов
```bash
netstat -tlnp | grep :8443
```

### Тест HTTPS доступности
```bash
curl -k https://194.87.236.174:8443
```

## 🔒 Безопасность

- Использует самоподписанный SSL сертификат
- Firewall настроен только для SSH (22) и HTTPS (8443)
- Все данные передаются по HTTPS

## 📝 Логи

Логи сохраняются в systemd journal и доступны через команды:
- `./manage.sh logs` - все логи
- `./manage.sh logs-telegram` - только Telegram бот
- `./manage.sh logs-https` - только HTTPS сервер

## 🤖 Telegram команды

- `/start` - Запуск бота
- `/help` - Справка
- `/status` - Статус системы

## 🔄 Автоматический запуск

Сервисы настроены для автоматического запуска при загрузке системы и автоматического перезапуска при сбоях.

## 📞 Поддержка

При возникновении проблем проверьте:
1. Статус сервисов: `./manage.sh status`
2. Логи: `./manage.sh logs`
3. Доступность портов: `netstat -tlnp | grep :8443`
4. Firewall: `ufw status` 