# Установка Django проекта

## 1. Подготовка сервера

```bash
# Создаем директории
mkdir -p /opt/driver
mkdir -p /var/log/gunicorn
mkdir -p /var/run/gunicorn
mkdir -p /var/log/nginx
```

## 2. Копирование файлов

```bash
# Копируем файлы проекта
cp -r * /opt/driver/
cp nginx.conf /etc/nginx/sites-available/driver
cp gunicorn_config.py /opt/driver/

# Создаем символическую ссылку для Nginx
ln -sf /etc/nginx/sites-available/driver /etc/nginx/sites-enabled/
```

## 3. Настройка Python окружения

```bash
# Переходим в директорию проекта
cd /opt/driver

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install django djangorestframework gunicorn

# Применяем миграции
python manage.py makemigrations
python manage.py migrate

# Собираем статические файлы
python manage.py collectstatic --noinput
```

## 4. Настройка сервисов

### Gunicorn

Создаем файл `/etc/systemd/system/driver.service`:

```ini
[Unit]
Description=Driver Django Application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/driver
Environment="PATH=/opt/driver/venv/bin"
ExecStart=/opt/driver/venv/bin/gunicorn -c gunicorn_config.py driver.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Nginx

Проверяем конфигурацию:
```bash
nginx -t
```

## 5. Запуск сервисов

```bash
# Перезагружаем systemd
systemctl daemon-reload

# Запускаем сервисы
systemctl restart nginx
systemctl enable driver
systemctl start driver
```

## 6. Проверка статуса

```bash
# Проверяем статус Nginx
systemctl status nginx

# Проверяем статус Django приложения
systemctl status driver

# Проверяем логи
tail -f /var/log/nginx/driver.error.log
tail -f /var/log/gunicorn/error.log
```

## 7. Проверка работы API

```bash
# Проверка включения/выключения отслеживания
curl -X POST http://194.87.236.174/api/tracking/toggle

# Проверка получения местоположения
curl "http://194.87.236.174/api/location?latitude=55.676803&longitude=37.52351"
``` 