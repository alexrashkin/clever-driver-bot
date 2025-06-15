#!/bin/bash

# Создаем директорию для бота
mkdir -p /opt/driver-bot

# Копируем файлы
cp bot.py /opt/driver-bot/
cp db.py /opt/driver-bot/
cp config.py /opt/driver-bot/
cp requirements.txt /opt/driver-bot/
cp driver-bot.service /etc/systemd/system/

# Создаем виртуальное окружение
cd /opt/driver-bot
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем директорию для логов
mkdir -p /var/log/driver-bot
touch /var/log/driver-bot/driver-bot.log
chmod 666 /var/log/driver-bot/driver-bot.log

# Перезагружаем systemd
systemctl daemon-reload

# Включаем и запускаем сервис
systemctl enable driver-bot
systemctl start driver-bot

echo "Установка завершена. Проверьте статус сервиса:"
echo "systemctl status driver-bot" 