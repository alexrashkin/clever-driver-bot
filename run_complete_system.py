#!/usr/bin/env python3
"""
Запуск полной системы Driver Bot
"""

import asyncio
import subprocess
import sys
import time
import signal
import os

def run_bot():
    """Запуск бота"""
    print("🤖 Запуск бота...")
    return subprocess.Popen([sys.executable, "bot_simple.py"])

def run_web():
    """Запуск веб-интерфейса"""
    print("🌐 Запуск веб-интерфейса...")
    return subprocess.Popen([sys.executable, "web_simple.py"])

def run_tracker():
    """Запуск автоматического трекера"""
    print("📍 Запуск автоматического трекера...")
    return subprocess.Popen([sys.executable, "auto_tracker.py"])

def main():
    print("🚗 ЗАПУСК ПОЛНОЙ СИСТЕМЫ DRIVER BOT")
    print("=" * 50)
    
    processes = []
    
    try:
        # Запускаем все компоненты
        print("1️⃣ Запуск бота...")
        bot_process = run_bot()
        processes.append(("Бот", bot_process))
        time.sleep(2)
        
        print("2️⃣ Запуск веб-интерфейса...")
        web_process = run_web()
        processes.append(("Веб-интерфейс", web_process))
        time.sleep(2)
        
        print("3️⃣ Запуск автоматического трекера...")
        tracker_process = run_tracker()
        processes.append(("Автотрекер", tracker_process))
        
        print("\n✅ Все компоненты запущены!")
        print("🌐 Веб-интерфейс: http://localhost:5000")
        print("🤖 Бот: готов к работе")
        print("📍 Автотрекер: активен")
        print("\n⏹️ Для остановки нажмите Ctrl+C")
        
        # Ждем завершения
        while True:
            time.sleep(1)
            
            # Проверяем, что все процессы работают
            for name, process in processes:
                if process.poll() is not None:
                    print(f"❌ {name} завершился с кодом {process.returncode}")
                    return
            
    except KeyboardInterrupt:
        print("\n⏹️ Остановка системы...")
        
        # Останавливаем все процессы
        for name, process in processes:
            print(f"🛑 Остановка {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print(f"✅ {name} остановлен")
            except subprocess.TimeoutExpired:
                print(f"⚠️ Принудительная остановка {name}...")
                process.kill()
        
        print("🎉 Система остановлена")

if __name__ == "__main__":
    main() 