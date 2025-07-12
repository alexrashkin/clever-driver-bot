#!/usr/bin/env python3
"""
Запуск Driver Bot с исправлением event loop
"""

import sys
import os
import asyncio

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main

if __name__ == "__main__":
    print("🚗 Запуск Driver Bot...")
    try:
        # Исправление для event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.close()
        except:
            pass
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1) 