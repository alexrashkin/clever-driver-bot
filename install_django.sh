#!/bin/bash

# Создаем директории
mkdir -p /opt/driver
mkdir -p /var/log/gunicorn
mkdir -p /var/run/gunicorn
mkdir -p /var/log/nginx

# Копируем файлы
cp -r * /opt/driver/
cp nginx.conf /etc/nginx/sites-available/driver
cp gunicorn_config.py /opt/driver/

# Создаем символическую ссылку для Nginx
ln -sf /etc/nginx/sites-available/driver /etc/nginx/sites-enabled/

# Создаем виртуальное окружение
cd /opt/driver
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install django djangorestframework gunicorn

# Применяем миграции
python manage.py makemigrations
python manage.py migrate

# Собираем статические файлы
python manage.py collectstatic --noinput

# Создаем сервис для Gunicorn
cat > /etc/systemd/system/driver.service << EOL
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
EOL

# Перезагружаем systemd
systemctl daemon-reload

# Запускаем сервисы
systemctl restart nginx
systemctl enable driver
systemctl start driver

echo "Установка завершена. Проверьте статус сервисов:"
echo "systemctl status nginx"
echo "systemctl status driver" 