# Clever Driver Bot - Docker Container
FROM python:3.9-slim

# Метаданные
LABEL maintainer="Clever Driver Bot"
LABEL description="Geolocation tracking bot with Telegram notifications"
LABEL version="1.0"

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов требований
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание пользователя без root привилегий
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Открытие порта
EXPOSE 8443

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Создание скрипта запуска
RUN echo '#!/bin/bash' > start.sh && \
    echo 'python telegram_bot_handler.py &' >> start.sh && \
    echo 'python https_simple_server.py' >> start.sh && \
    chmod +x start.sh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -k https://localhost:8443/ || exit 1

# Запуск
CMD ["./start.sh"] 