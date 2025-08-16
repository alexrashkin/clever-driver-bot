import os
import secrets

# Функция для логирования в файл
def log_to_file(message):
    # Разрешаем переопределять путь через переменную окружения
    log_path = os.environ.get('CONFIG_DEBUG_LOG', '/tmp/config_debug.log')
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
    except Exception:
        # Фолбэк на консоль при невозможности записать файл
        pass
    print(message)

# Загружаем переменные окружения из .env файла
def load_env_file():
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    log_to_file(f"🔍 CONFIG: Проверяем .env файл: {env_file}")
    if os.path.exists(env_file):
        log_to_file("✅ CONFIG: .env файл найден, загружаем переменные...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key.lower().startswith('export '):
                        key = key[7:].strip()
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    os.environ[key] = value
                    os.environ[key.upper()] = value
                    log_to_file(f"📝 CONFIG: Загружена переменная: {key}")
        log_to_file(f"📧 CONFIG: EMAIL_ENABLED = {os.environ.get('EMAIL_ENABLED', 'НЕ УСТАНОВЛЕН')}")
    else:
        log_to_file("❌ CONFIG: .env файл не найден")

# Загружаем .env файл
load_env_file()

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
    
    # Извлекаем bot_id из токена (первая часть до двоеточия)
    TELEGRAM_BOT_ID = TELEGRAM_BOT_TOKEN.split(':')[0] if TELEGRAM_BOT_TOKEN and ':' in TELEGRAM_BOT_TOKEN else ""
    
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
    SSL_CERT_FILE = os.getenv("SSL_CERT_FILE", "")
    SSL_KEY_FILE = os.getenv("SSL_KEY_FILE", "")
    SSL_ENABLED = os.getenv("SSL_ENABLED", "False").lower() == "true"
    
    # Координаты по умолчанию (Красная площадь)
    WORK_LATITUDE = 55.7539  # Красная площадь
    WORK_LONGITUDE = 37.6208  # Красная площадь
    WORK_RADIUS = 100  # метров
    
    # Логирование безопасности
    SECURITY_LOG_FILE = "security.log"
    LOG_SECURITY_EVENTS = os.getenv("LOG_SECURITY_EVENTS", "True").lower() == "true"
    
    # Email настройки
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "")
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Умный водитель")

config = Config()

# Отладочная информация
print(f"🔧 CONFIG_DEBUG: EMAIL_ENABLED = {config.EMAIL_ENABLED}")
print(f"🔧 CONFIG_DEBUG: os.environ.get('EMAIL_ENABLED') = {os.environ.get('EMAIL_ENABLED')}")
print(f"🔧 CONFIG_DEBUG: type(config.EMAIL_ENABLED) = {type(config.EMAIL_ENABLED)}")
