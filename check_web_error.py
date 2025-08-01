#!/usr/bin/env python3
"""
Проверка ошибок веб-приложения
"""

import subprocess
import sys

def check_web_error():
    """Проверяет ошибки веб-приложения"""
    
    print("=== ПРОВЕРКА ОШИБОК ВЕБ-ПРИЛОЖЕНИЯ ===")
    
    try:
        # Получаем последние логи веб-сервиса
        result = subprocess.run([
            'journalctl', '-u', 'driver-web', '-n', '30', '--no-pager'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Последние логи веб-сервиса:")
            print(result.stdout)
        else:
            print("Ошибка получения логов:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("\n=== ПРОВЕРКА СТАТУСА СЕРВИСА ===")
    
    try:
        result = subprocess.run([
            'systemctl', 'status', 'driver-web'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Статус веб-сервиса:")
            print(result.stdout)
        else:
            print("Ошибка получения статуса:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("\n=== ПРОВЕРКА ПРОЦЕССОВ ===")
    
    try:
        result = subprocess.run([
            'ps', 'aux', '|', 'grep', 'python'
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print("Python процессы:")
            print(result.stdout)
        else:
            print("Ошибка получения процессов:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    check_web_error() 