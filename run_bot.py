#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска бота
Используется systemd сервисом
"""
import sys
import os
import asyncio
import nest_asyncio

# Применяем nest_asyncio для решения проблем с event loop
nest_asyncio.apply()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bot.main import main

if __name__ == "__main__":
    try:
        print("🚀 Запуск бота через run_bot.py...")
        # Создаем новый event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем main() в этом loop
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            loop.close()
        except:
            pass 