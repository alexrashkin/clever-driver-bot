import os

class Config:
    # База данных
    DATABASE_PATH = "driver.db"
    
    # Веб-сервер
    WEB_HOST = "0.0.0.0"
    WEB_PORT = 5000
    WEB_SECRET_KEY = "your-secret-key-change-this-in-production"
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "clever_driver_bot")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # Алиас для совместимости
    
    # Рабочие координаты
    WORK_LATITUDE = float(os.getenv("WORK_LATITUDE", "55.7558"))
    WORK_LONGITUDE = float(os.getenv("WORK_LONGITUDE", "37.6176"))
    WORK_RADIUS = float(os.getenv("WORK_RADIUS", "100"))
    
    # Email настройки
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Driver Bot")
    EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "")
    
    # Логирование
    LOG_LEVEL = "INFO"
    LOG_FILE = "app.log"

config = Config()
