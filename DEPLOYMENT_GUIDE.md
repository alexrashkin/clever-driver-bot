# 🚗 Clever Driver Bot - Руководство по деплою на ВМ

## 📦 Содержимое пакета

Архив `clever-driver-bot-vm-deploy.tar.gz` содержит:

### Основные файлы:
- `https_simple_server.py` - HTTPS веб-сервер
- `geolocation_bot.py` - логика геолокации
- `telegram_bot_handler.py` - Telegram бот
- `geo_locations.json` - настройки геозон

### Системные файлы:
- `check_status.py` - проверка статуса
- `restart_system.py` - перезапуск системы
- `requirements.txt` - Python зависимости

### Деплой файлы:
- `deploy_setup.sh` - автоматическая установка Linux
- `config_vm.py` - настройка IP адреса
- `Dockerfile` - для Docker контейнера
- `docker-compose.yml` - Docker Compose конфигурация

## 🔧 Варианты деплоя

### Вариант 1: Автоматическая установка на Linux

```bash
# 1. Скопируйте архив на ВМ
scp clever-driver-bot-vm-deploy.tar.gz user@VM_IP:/tmp/

# 2. Подключитесь к ВМ
ssh user@VM_IP

# 3. Распакуйте архив
cd /tmp
tar -xzf clever-driver-bot-vm-deploy.tar.gz

# 4. Запустите автоустановку
chmod +x deploy_setup.sh
sudo ./deploy_setup.sh

# 5. Скопируйте файлы проекта
sudo cp *.py *.json *.md /opt/clever-driver-bot/

# 6. Настройте IP адрес
cd /opt/clever-driver-bot
python3 config_vm.py

# 7. Запустите сервисы
./manage.sh start
```

### Вариант 2: Docker контейнер

```bash
# 1. Установите Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 2. Распакуйте проект
tar -xzf clever-driver-bot-vm-deploy.tar.gz
cd clever-driver-bot-vm-deploy

# 3. Настройте IP адрес
python3 config_vm.py YOUR_VM_IP

# 4. Запустите контейнер
docker-compose up -d

# 5. Проверьте статус
docker-compose ps
docker-compose logs -f
```

### Вариант 3: Ручная установка

```bash
# 1. Установите Python 3.8+
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 2. Создайте проект
mkdir /opt/clever-driver-bot
cd /opt/clever-driver-bot

# 3. Распакуйте файлы
tar -xzf /path/to/clever-driver-bot-vm-deploy.tar.gz

# 4. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 5. Установите зависимости
pip install -r requirements.txt

# 6. Настройте IP
python3 config_vm.py

# 7. Запустите сервисы
python telegram_bot_handler.py &
python https_simple_server.py
```

## 🌐 Настройка сети

### Открытие портов:

#### Ubuntu/Debian (UFW):
```bash
sudo ufw allow 8443/tcp
sudo ufw enable
```

#### CentOS/RHEL (FirewallD):
```bash
sudo firewall-cmd --permanent --add-port=8443/tcp
sudo firewall-cmd --reload
```

#### Облачные провайдеры:
- **AWS**: добавьте правило в Security Group для порта 8443
- **Azure**: добавьте правило в Network Security Group
- **Google Cloud**: создайте firewall rule для tcp:8443
- **DigitalOcean**: добавьте правило в Firewall

## 📱 Обновление Telegram бота

После деплоя на ВМ обновите IP адрес в Telegram боте:

```bash
# Автоматически через скрипт
python3 config_vm.py YOUR_VM_IP

# Или вручную в файлах:
# - https_simple_server.py: найдите '192.168.0.104' и замените на IP ВМ
# - telegram_bot_handler.py: обновите ссылки на новый IP
```

## 🔍 Проверка работы

### 1. Проверка статуса:
```bash
# Автоматическая установка
cd /opt/clever-driver-bot
./manage.sh status

# Docker
docker-compose ps

# Ручная установка
ps aux | grep python
```

### 2. Проверка портов:
```bash
netstat -tlnp | grep 8443
# Или
ss -tlnp | grep 8443
```

### 3. Проверка HTTPS сервера:
```bash
curl -k https://YOUR_VM_IP:8443/
```

### 4. Проверка логов:
```bash
# Автоматическая установка
./manage.sh logs

# Docker
docker-compose logs -f

# Ручная установка
tail -f /var/log/syslog | grep python
```

## 🚀 Управление сервисами

### Автоматическая установка (systemd):
```bash
./manage.sh start      # Запуск
./manage.sh stop       # Остановка
./manage.sh restart    # Перезапуск
./manage.sh status     # Статус
./manage.sh logs       # Логи
```

### Docker:
```bash
docker-compose up -d        # Запуск
docker-compose down         # Остановка
docker-compose restart      # Перезапуск
docker-compose ps           # Статус
docker-compose logs -f      # Логи
```

## 🔧 Устранение проблем

### Проблема: Порт 8443 уже занят
```bash
sudo lsof -i :8443
sudo kill -9 PID_ПРОЦЕССА
```

### Проблема: SSL сертификат не работает
```bash
# Используйте curl с -k для игнорирования SSL ошибок
curl -k https://YOUR_VM_IP:8443/
```

### Проблема: Telegram бот не отвечает
```bash
# Проверьте логи
journalctl -u clever-telegram-bot.service -f
```

### Проблема: Нет доступа к серверу
```bash
# Проверьте файрволл
sudo ufw status
sudo iptables -L

# Проверьте что сервер слушает на всех интерфейсах
netstat -tlnp | grep 8443
```

## 📊 Мониторинг

### Настройка автозапуска:
```bash
# Уже настроено в deploy_setup.sh
sudo systemctl enable clever-telegram-bot.service
sudo systemctl enable clever-https-server.service
```

### Проверка работы каждые 5 минут:
```bash
# Добавьте в crontab
crontab -e

# Добавьте строку:
*/5 * * * * curl -k https://localhost:8443/ > /dev/null 2>&1 || systemctl restart clever-https-server.service
```

## 🎯 Результат

После успешного деплоя:
- ✅ HTTPS сервер доступен по адресу: `https://YOUR_VM_IP:8443`
- ✅ Telegram бот работает с новым IP
- ✅ Геолокация и уведомления функционируют
- ✅ Система автоматически запускается при перезагрузке ВМ
- ✅ Логи доступны через systemd/docker

## 🔄 Обновление

Для обновления проекта:
```bash
# 1. Остановите сервисы
./manage.sh stop

# 2. Создайте бэкап
cp -r /opt/clever-driver-bot /opt/clever-driver-bot.backup

# 3. Обновите файлы
# Скопируйте новые версии файлов

# 4. Запустите сервисы
./manage.sh start
```

---

**📞 Поддержка**: В случае проблем проверьте логи и статус сервисов. Система спроектирована для стабильной работы 24/7. 