#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска веб-приложения
Используется systemd сервисом
"""
import sys
import os

# Функция для логирования в файл
def log_to_file(message):
    with open('/tmp/run_web_debug.log', 'a', encoding='utf-8') as f:
        f.write(f"{message}\n")
    print(message)

# Загружаем переменные окружения из .env файла ПЕРЕД всеми импортами
def load_env_file():
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    log_to_file(f"🔍 RUN_WEB: Проверяем .env файл: {env_file}")
    if os.path.exists(env_file):
        log_to_file("✅ RUN_WEB: .env файл найден, загружаем переменные...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    log_to_file(f"📝 RUN_WEB: Загружена переменная: {key}")
        log_to_file(f"📧 RUN_WEB: EMAIL_ENABLED = {os.environ.get('EMAIL_ENABLED', 'НЕ УСТАНОВЛЕН')}")
    else:
        log_to_file("❌ RUN_WEB: .env файл не найден")

# Загружаем .env файл ПЕРЕД всеми импортами
load_env_file()

import asyncio

# Пытаемся импортировать nest_asyncio, если не установлен - пропускаем
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    log_to_file("⚠️ nest_asyncio не установлен, пропускаем...")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        log_to_file("🌐 Запуск веб-приложения через run_web.py...")
        
        # Запускаем Flask приложение
        from web.app import app
        from config.settings import config
        
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=False
        )
    except KeyboardInterrupt:
        log_to_file("\n🛑 Остановка веб-приложения...")
    except Exception as e:
        log_to_file(f"❌ Ошибка запуска веб-приложения: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 