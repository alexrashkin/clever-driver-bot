#!/usr/bin/env python3
"""
Альтернативный запуск Driver Bot с nest_asyncio
"""

import sys
import os
import asyncio
import nest_asyncio
import signal

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем nest_asyncio для разрешения вложенных event loops
try:
    nest_asyncio.apply()
except ImportError:
    print("Установите nest-asyncio: pip install nest-asyncio")
    sys.exit(1)

from bot.main import main

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n⏹️ Получен сигнал завершения, останавливаем бота...")
    sys.exit(0)

if __name__ == "__main__":
    print("🚗 Запуск Driver Bot...")
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Проверяем, есть ли уже запущенный event loop
        try:
            loop = asyncio.get_running_loop()
            print("⚠️ Обнаружен запущенный event loop, используем его")
        except RuntimeError:
            # Создаем новый event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print("✅ Создан новый event loop")
        
        # Запускаем основную функцию
        loop.run_until_complete(main())
        
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
    finally:
        # Корректно закрываем event loop
        try:
            if loop and not loop.is_closed():
                loop.close()
        except Exception as e:
            print(f"⚠️ Ошибка при закрытии event loop: {e}") 