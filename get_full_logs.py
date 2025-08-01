#!/usr/bin/env python3
"""
Получение полных логов
"""

import subprocess
import sys

def get_full_logs():
    """Получает полные логи"""
    
    print("=== ПОЛНЫЕ ЛОГИ ВЕБ-СЕРВИСА ===")
    
    try:
        # Получаем больше строк логов
        result = subprocess.run([
            'journalctl', '-u', 'driver-web', '-n', '50', '--no-pager'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Ошибка получения логов:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("\n=== ПОСЛЕДНИЕ ОШИБКИ ===")
    
    try:
        # Получаем только ошибки
        result = subprocess.run([
            'journalctl', '-u', 'driver-web', '-p', 'err', '-n', '20', '--no-pager'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Ошибка получения ошибок:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    get_full_logs() 