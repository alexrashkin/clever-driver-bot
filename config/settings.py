import os
import secrets

class Config:
    # База данных
    DATABASE_PATH = "driver.db"
    
    # Веб-сервер
    WEB_HOST = "0.0.0.0"
    WEB_PORT = 5000
    WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", secrets.token_hex(32))
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "clever_driver_bot")
    TELEGRAM_TOKEN = TELEGRAM_BOT_TOKEN  # Алиас для совместимости
    
    # Рабочие координаты
    WORK_LATITUDE = float(os.getenv("WORK_LATITUDE", "55.7558"))
    WORK_LONGITUDE = float(os.getenv("WORK_LONGITUDE", "37.6176"))
    WORK_RADIUS = float(os.getenv("WORK_RADIUS", "100"))
    
    # Логирование
    LOG_LEVEL = "INFO"
    LOG_FILE = "app.log"

config = Config()
