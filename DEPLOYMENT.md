# 🚀 Развертывание Driver Bot на сервере

## Варианты развертывания

### 1. Развертывание с Docker (Рекомендуется)

#### Предварительные требования
- Ubuntu 18.04+ или другой Linux дистрибутив
- SSH доступ к серверу
- Права sudo

#### Быстрое развертывание
```bash
# Клонирование репозитория
git clone https://github.com/alexrashkin/clever-driver-bot.git
cd clever-driver-bot

# Запуск развертывания
chmod +x deploy_server.sh
./deploy_server.sh
```

#### Ручное развертывание с Docker
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Создание директорий
mkdir -p logs data

# Сборка и запуск
docker-compose up --build -d

# Проверка статуса
docker-compose ps
docker-compose logs -f
```

### 2. Ручное развертывание без Docker

#### Быстрое развертывание
```bash
# Клонирование репозитория
git clone https://github.com/alexrashkin/clever-driver-bot.git
cd clever-driver-bot

# Запуск развертывания
chmod +x deploy_manual.sh
./deploy_manual.sh
```

#### Ручное развертывание пошагово
```bash
# 1. Обновление системы
sudo apt-get update && sudo apt-get upgrade -y

# 2. Установка зависимостей
sudo apt-get install -y python3 python3-pip python3-venv nginx

# 3. Создание пользователя
sudo useradd -m -s /bin/bash driverbot
sudo usermod -aG sudo driverbot

# 4. Создание директории приложения
sudo mkdir -p /opt/driver-bot
sudo chown driverbot:driverbot /opt/driver-bot

# 5. Копирование файлов
sudo cp -r . /opt/driver-bot/
sudo chown -R driverbot:driverbot /opt/driver-bot

# 6. Настройка Python окружения
cd /opt/driver-bot
sudo -u driverbot python3 -m venv venv
sudo -u driverbot ./venv/bin/pip install -r requirements.txt

# 7. Создание systemd сервиса
sudo tee /etc/systemd/system/driver-bot.service > /dev/null <<EOF
[Unit]
Description=Driver Bot Web Interface
After=network.target

[Service]
Type=simple
User=driverbot
WorkingDirectory=/opt/driver-bot
Environment=PATH=/opt/driver-bot/venv/bin
ExecStart=/opt/driver-bot/venv/bin/python web_simple.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. Настройка Nginx
sudo tee /etc/nginx/sites-available/driver-bot > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /opt/driver-bot/static/;
    }
}
EOF

# 9. Активация сервисов
sudo ln -sf /etc/nginx/sites-available/driver-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl daemon-reload
sudo systemctl enable driver-bot
sudo systemctl start driver-bot
sudo systemctl restart nginx

# 10. Настройка firewall
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
```

## Настройка переменных окружения

### Создание файла .env
```bash
cp env.example .env
nano .env
```

### Настройка Telegram Bot
1. Создайте бота через @BotFather в Telegram
2. Получите токен бота
3. Добавьте бота в нужный чат
4. Получите ID чата (можно использовать @userinfobot)
5. Обновите переменные в .env файле

## Проверка работы

### Проверка сервисов
```bash
# Docker
docker-compose ps
docker-compose logs -f

# Ручное развертывание
sudo systemctl status driver-bot
sudo systemctl status nginx
sudo journalctl -u driver-bot -f
```

### Проверка веб-интерфейса
- Откройте в браузере: `http://YOUR_SERVER_IP`
- Мобильная страница: `http://YOUR_SERVER_IP/mobile_tracker.html`

## Управление сервисами

### Docker
```bash
# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Обновление
git pull
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f
```

### Ручное развертывание
```bash
# Остановка
sudo systemctl stop driver-bot

# Запуск
sudo systemctl start driver-bot

# Перезапуск
sudo systemctl restart driver-bot

# Просмотр логов
sudo journalctl -u driver-bot -f

# Обновление
cd /opt/driver-bot
git pull
sudo systemctl restart driver-bot
```

## Безопасность

### SSL сертификат (Let's Encrypt)
```bash
# Установка Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавить строку: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall
```bash
# Настройка UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Мониторинг

### Логи
- Docker: `docker-compose logs -f`
- Ручное: `sudo journalctl -u driver-bot -f`

### Статус
- Docker: `docker-compose ps`
- Ручное: `sudo systemctl status driver-bot`

### Ресурсы
```bash
# Использование памяти
free -h

# Использование диска
df -h

# Процессы
htop
```

## Устранение неполадок

### Проблемы с Docker
```bash
# Очистка контейнеров
docker system prune -a

# Пересборка
docker-compose down
docker-compose up --build -d
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

# Проверка портов
sudo netstat -tlnp | grep :5000

# Перезапуск
sudo systemctl restart driver-bot
```

## Обновление

### Docker
```bash
git pull
docker-compose down
docker-compose up --build -d
```

### Ручное развертывание
```bash
cd /opt/driver-bot
git pull
sudo systemctl restart driver-bot
```

## Резервное копирование

### База данных
```bash
# Docker
docker-compose exec driver-bot sqlite3 data/driver_bot.db ".backup backup.db"

# Ручное
sudo -u driverbot sqlite3 /opt/driver-bot/data/driver_bot.db ".backup backup.db"
```

### Конфигурация
```bash
# Копирование важных файлов
cp .env backup/
cp /etc/systemd/system/driver-bot.service backup/
cp /etc/nginx/sites-available/driver-bot backup/
``` 