#!/bin/bash

echo "=== Установка Telegram бота на новом сервере ==="

# Обновляем систему
echo "Обновляем систему..."
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
echo "Устанавливаем Python и зависимости..."
apt install -y python3 python3-pip python3-venv git curl wget nginx

# Создаем директорию для бота
echo "Создаем директорию для бота..."
mkdir -p /opt/driver-bot
cd /opt/driver-bot

# Создаем виртуальное окружение
echo "Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip install --upgrade pip
pip install python-telegram-bot pytz requests

echo "=== Установка завершена ==="
echo "Теперь нужно загрузить файлы бота" 