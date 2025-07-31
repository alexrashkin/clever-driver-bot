#!/usr/bin/env python3
"""
Диагностика проблем с ботом
"""

import sys
import os

def check_imports():
    """Проверяет импорты необходимых модулей"""
    print("🔍 Проверка импортов...")
    
    try:
        import asyncio
        print("✅ asyncio")
    except ImportError as e:
        print(f"❌ asyncio: {e}")
        return False
    
    try:
        import nest_asyncio
        print("✅ nest_asyncio")
    except ImportError as e:
        print(f"❌ nest_asyncio: {e}")
        return False
    
    try:
        import telegram
        print("✅ python-telegram-bot")
    except ImportError as e:
        print(f"❌ python-telegram-bot: {e}")
        return False
    
    try:
        import sqlite3
        print("✅ sqlite3")
    except ImportError as e:
        print(f"❌ sqlite3: {e}")
        return False
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    return True

def check_config():
    """Проверяет конфигурацию"""
    print("\n🔧 Проверка конфигурации...")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config.settings import config
        
        print(f"✅ TELEGRAM_TOKEN: {'*' * 10}{config.TELEGRAM_TOKEN[-4:]}")
        print(f"✅ TELEGRAM_BOT_USERNAME: {config.TELEGRAM_BOT_USERNAME}")
        print(f"✅ TELEGRAM_BOT_ID: {config.TELEGRAM_BOT_ID}")
        print(f"✅ WORK_LATITUDE: {config.WORK_LATITUDE}")
        print(f"✅ WORK_LONGITUDE: {config.WORK_LONGITUDE}")
        print(f"✅ WORK_RADIUS: {config.WORK_RADIUS}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def check_database():
    """Проверяет базу данных"""
    print("\n🗄️ Проверка базы данных...")
    
    try:
        import sqlite3
        db_path = "driver.db"
        
        if not os.path.exists(db_path):
            print(f"❌ База данных не найдена: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Найдено таблиц: {len(tables)}")
        
        for table in tables:
            print(f"  - {table[0]}")
        
        # Проверяем таблицу users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Пользователей в базе: {user_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

def check_bot_modules():
    """Проверяет модули бота"""
    print("\n🤖 Проверка модулей бота...")
    
    try:
        from bot.database import db
        print("✅ bot.database")
    except Exception as e:
        print(f"❌ bot.database: {e}")
        return False
    
    try:
        from bot.handlers import start_command
        print("✅ bot.handlers")
    except Exception as e:
        print(f"❌ bot.handlers: {e}")
        return False
    
    try:
        from bot.main import main
        print("✅ bot.main")
    except Exception as e:
        print(f"❌ bot.main: {e}")
        return False
    
    return True

def test_bot_connection():
    """Тестирует подключение к Telegram API"""
    print("\n📡 Тестирование подключения к Telegram...")
    
    try:
        from config.settings import config
        import requests
        
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Бот доступен: @{bot_info.get('username')}")
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Диагностика бота Умный водитель")
    print("=" * 50)
    
    all_ok = True
    
    # Проверяем импорты
    if not check_imports():
        all_ok = False
    
    # Проверяем конфигурацию
    if not check_config():
        all_ok = False
    
    # Проверяем базу данных
    if not check_database():
        all_ok = False
    
    # Проверяем модули бота
    if not check_bot_modules():
        all_ok = False
    
    # Тестируем подключение
    if not test_bot_connection():
        all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ Все проверки пройдены! Бот должен работать.")
        print("\n💡 Если бот все равно не запускается:")
        print("1. Проверьте логи: python run_bot.py 2>&1 | tee bot.log")
        print("2. Проверьте права доступа к файлам")
        print("3. Убедитесь, что виртуальное окружение активировано")
    else:
        print("❌ Найдены проблемы. Исправьте их перед запуском бота.")
        print("\n💡 Рекомендации:")
        print("1. Установите недостающие зависимости: pip install -r requirements.txt")
        print("2. Проверьте файл .env с переменными окружения")
        print("3. Убедитесь, что база данных существует и доступна") 