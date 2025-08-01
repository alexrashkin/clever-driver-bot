#!/usr/bin/env python3
"""
Скрипт для запуска веб-интерфейса
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Добавляем путь к web директории
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web'))

from app import app
from config.settings import config

if __name__ == "__main__":
    print("🌐 Запуск веб-интерфейса...")
    print(f"📍 Адрес: http://{config.WEB_HOST}:{config.WEB_PORT}")
    try:
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=False
        )
    except KeyboardInterrupt:
        print("\n⏹️ Веб-интерфейс остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1) 