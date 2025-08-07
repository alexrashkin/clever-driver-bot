#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска веб-приложения
Используется systemd сервисом
"""
import sys
import os
import asyncio

# Пытаемся импортировать nest_asyncio, если не установлен - пропускаем
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    print("⚠️ nest_asyncio не установлен, пропускаем...")

# Загружаем переменные окружения из .env файла
def load_env_file():
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    print(f"🔍 Проверяем .env файл: {env_file}")
    if os.path.exists(env_file):
        print("✅ .env файл найден, загружаем переменные...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"📝 Загружена переменная: {key}")
        print(f"📧 EMAIL_ENABLED = {os.environ.get('EMAIL_ENABLED', 'НЕ УСТАНОВЛЕН')}")
    else:
        print("❌ .env файл не найден")

# Загружаем .env файл
load_env_file()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        print("🌐 Запуск веб-приложения через run_web.py...")
        
        # Запускаем Flask приложение
        from web.app import app
        from config.settings import config
        
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Остановка веб-приложения...")
    except Exception as e:
        print(f"❌ Ошибка запуска веб-приложения: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 