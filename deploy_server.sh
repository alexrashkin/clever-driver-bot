#!/bin/bash

echo "🚀 Развертывание Driver Bot на сервере..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаем..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker установлен. Перезапустите терминал и запустите скрипт снова."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаем..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose установлен."
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p logs data

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка и запуск
echo "🔨 Сборка и запуск контейнеров..."
docker-compose up --build -d

# Проверка статуса
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса контейнеров
echo "📊 Статус контейнеров:"
docker-compose ps

# Проверка логов
echo "📋 Последние логи:"
docker-compose logs --tail=20

echo ""
echo "✅ Развертывание завершено!"
echo "🌐 Веб-интерфейс доступен по адресу: http://YOUR_SERVER_IP:5000"
echo "📱 Мобильная страница: http://YOUR_SERVER_IP:5000/mobile_tracker.html"
echo ""
echo "📝 Полезные команды:"
echo "  docker-compose logs -f    # Просмотр логов в реальном времени"
echo "  docker-compose down       # Остановка сервисов"
echo "  docker-compose restart    # Перезапуск сервисов"
echo "  docker-compose up -d      # Запуск сервисов" 