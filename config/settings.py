import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Основные настройки приложения"""
    
    # Telegram Bot
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc')
    TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', 'Clever_driver_bot')
    TELEGRAM_BOT_ID = os.getenv('TELEGRAM_BOT_ID', '7824059826')  # ID бота (первая часть токена)
    
    # Chat ID для уведомлений
    NOTIFICATION_CHAT_ID = os.getenv('NOTIFICATION_CHAT_ID', '')
    
    # Прокси настройки (для обхода блокировки)
    USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_URL = os.getenv('PROXY_URL', '')  # например: socks5://127.0.0.1:1080
    
    # Координаты работы
    WORK_LATITUDE = float(os.getenv('WORK_LATITUDE', '55.676803'))
    WORK_LONGITUDE = float(os.getenv('WORK_LONGITUDE', '37.52351'))
    WORK_RADIUS = int(os.getenv('WORK_RADIUS', '100'))  # метров
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///driver.db')
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'driver-bot.log')  # Изменено для работы на разных ОС
    
    # Интервалы
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '5'))  # секунды
    
    # Веб-интерфейс
    WEB_HOST = os.getenv('WEB_HOST', '127.0.0.1')
    WEB_PORT = int(os.getenv('WEB_PORT', '5000'))
    WEB_SECRET_KEY = os.getenv('WEB_SECRET_KEY', 'clever-driver-secret-key-2024-very-secure-and-long')

# Создаем экземпляр конфигурации
config = Config() 