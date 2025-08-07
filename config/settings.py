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
    
    # Логирование
    LOG_LEVEL = "INFO"
    LOG_FILE = "app.log"
    
    # Безопасность
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_MAX_AGE = 3600 * 24 * 7  # 7 дней
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    LOGIN_RATE_LIMIT_REQUESTS = int(os.getenv("LOGIN_RATE_LIMIT_REQUESTS", "5"))
    LOGIN_RATE_LIMIT_WINDOW = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW", "300"))
    
    # IP блокировка
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "10"))
    BLOCK_DURATION_MINUTES = int(os.getenv("BLOCK_DURATION_MINUTES", "60"))
    
    # Пароли
    MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
    REQUIRE_SPECIAL_CHARS = os.getenv("REQUIRE_SPECIAL_CHARS", "True").lower() == "true"
    
    # HTTPS
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "False").lower() == "true"
    
    # Логирование безопасности
    SECURITY_LOG_FILE = "security.log"
    LOG_SECURITY_EVENTS = os.getenv("LOG_SECURITY_EVENTS", "True").lower() == "true"

config = Config()
