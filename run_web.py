#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска веб-приложения
Используется systemd сервисом
"""
import sys
import os
import asyncio
import nest_asyncio

# Применяем nest_asyncio для решения проблем с event loop
nest_asyncio.apply()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        print("🌐 Запуск веб-приложения через run_web.py...")
        from web.app import app
        
        # Запускаем Flask приложение
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("⏹️ Веб-приложение остановлено пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска веб-приложения: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 