import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Основные настройки приложения"""
    
    # Telegram Bot
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc')
    
    # Координаты работы
    WORK_LATITUDE = float(os.getenv('WORK_LATITUDE', '55.676803'))
    WORK_LONGITUDE = float(os.getenv('WORK_LONGITUDE', '37.52351'))
    WORK_RADIUS = int(os.getenv('WORK_RADIUS', '100'))  # метров
    
    # ID чатов
    DRIVER_CHAT_ID = int(os.getenv('DRIVER_CHAT_ID', '946872573'))
    NOTIFICATION_CHAT_ID = int(os.getenv('NOTIFICATION_CHAT_ID', '1623256768'))
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///driver.db')
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'driver-bot.log')
    
    # Интервалы
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))  # секунды
    
    # Веб-интерфейс
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', '5000'))
    WEB_SECRET_KEY = os.getenv('WEB_SECRET_KEY', 'your-secret-key-here')

# Создаем экземпляр конфигурации
config = Config() 