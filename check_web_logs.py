#!/usr/bin/env python3
"""
Проверка логов веб-сервиса
"""

import subprocess
import sys

def check_web_logs():
    """Проверяет логи веб-сервиса"""
    
    print("=== ПРОВЕРКА ЛОГОВ ВЕБ-СЕРВИСА ===")
    
    try:
        # Получаем последние логи
        result = subprocess.run([
            'journalctl', '-u', 'driver-web', '-n', '20', '--no-pager'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Последние логи веб-сервиса:")
            print(result.stdout)
        else:
            print("Ошибка получения логов:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("\n=== РУЧНОЙ ЗАПУСК ВЕБ-ПРИЛОЖЕНИЯ ===")
    
    try:
        # Пробуем запустить вручную
        result = subprocess.run([
            'python3', 'run_web.py'
        ], capture_output=True, text=True, timeout=10)
        
        print("Вывод:")
        print(result.stdout)
        print("Ошибки:")
        print(result.stderr)
        
    except subprocess.TimeoutExpired:
        print("Веб-приложение запустилось (таймаут)")
    except Exception as e:
        print(f"Ошибка запуска: {e}")

if __name__ == "__main__":
    check_web_logs() 