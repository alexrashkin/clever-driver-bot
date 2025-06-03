#!/usr/bin/env python3
"""
Скрипт для перезапуска всей системы Clever Driver Bot
Останавливает все процессы и запускает только нужные
"""

import subprocess
import time
import sys
import os

def kill_python_processes():
    """Остановка всех Python процессов кроме текущего"""
    print("🛑 Остановка всех Python процессов...")
    current_pid = os.getpid()
    
    try:
        # Получаем список всех python.exe процессов
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
        killed_count = 0
        
        for line in lines:
            if line:
                parts = line.replace('"', '').split(',')
                if len(parts) >= 2:
                    pid = int(parts[1])
                    if pid != current_pid:  # Не убиваем себя
                        try:
                            subprocess.run(["taskkill", "/PID", str(pid), "/F"], 
                                         capture_output=True)
                            killed_count += 1
                            print(f"  ✅ Остановлен процесс PID {pid}")
                        except:
                            pass
        
        print(f"🔥 Остановлено {killed_count} процессов")
        
    except Exception as e:
        print(f"❌ Ошибка при остановке процессов: {e}")

def wait_for_ports_free():
    """Ждем освобождения портов"""
    print("⏳ Ожидание освобождения портов...")
    time.sleep(3)

def start_servers():
    """Запуск нужных серверов"""
    print("🚀 Запуск серверов...")
    
    # Запуск HTTPS сервера для iPhone
    print("  📱 Запуск HTTPS сервера (порт 8444)...")
    subprocess.Popen([
        sys.executable, "https_iphone_server.py"
    ], cwd=os.getcwd())
    
    time.sleep(2)
    
    # Запуск обновленного Telegram бота
    print("  🤖 Запуск Telegram бота...")
    subprocess.Popen([
        sys.executable, "telegram_bot_handler.py"
    ], cwd=os.getcwd())
    
    time.sleep(2)

def check_status():
    """Проверка статуса системы"""
    print("🔍 Проверка статуса...")
    subprocess.run([sys.executable, "check_status.py"])

def main():
    """Главная функция"""
    print("="*60)
    print("🔄 ПЕРЕЗАПУСК CLEVER DRIVER BOT СИСТЕМЫ")
    print("="*60)
    
    # Остановка процессов
    kill_python_processes()
    
    # Ожидание
    wait_for_ports_free()
    
    # Запуск серверов
    start_servers()
    
    # Проверка
    print("\n" + "="*60)
    check_status()
    
    print("\n" + "="*60)
    print("✅ СИСТЕМА ПЕРЕЗАПУЩЕНА!")
    print("📱 Telegram бот: @Clever_driver_bot")
    print("🔒 HTTPS: https://192.168.0.104:8444")
    print("🌐 HTTP: http://192.168.0.104:8080 (если нужен)")
    print("="*60)
    print("💡 Теперь попробуйте команду /start в боте!")

if __name__ == "__main__":
    main() 