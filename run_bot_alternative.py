#!/usr/bin/env python3
"""
Альтернативный запуск Driver Bot с nest_asyncio
"""

import sys
import os
import asyncio
import nest_asyncio

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем nest_asyncio для разрешения вложенных event loops
try:
    nest_asyncio.apply()
except ImportError:
    print("Установите nest-asyncio: pip install nest-asyncio")
    sys.exit(1)

from bot.main import main

if __name__ == "__main__":
    print("🚗 Запуск Driver Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1) 