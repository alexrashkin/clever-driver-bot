#!/usr/bin/env python3
"""
Запуск упрощенного Driver Bot
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_simple import main
import asyncio

if __name__ == "__main__":
    print("🚗 Запуск упрощенного Driver Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1) 