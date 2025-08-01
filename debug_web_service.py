#!/usr/bin/env python3
"""
Диагностика проблем с веб-сервисом
"""

import os
import sys

def debug_web_service():
    """Диагностирует проблемы с веб-сервисом"""
    
    print("=== ДИАГНОСТИКА ВЕБ-СЕРВИСА ===")
    
    # 1. Проверяем файлы
    print("\n1. ПРОВЕРКА ФАЙЛОВ:")
    
    files_to_check = [
        'web/app.py',
        'config/settings.py',
        'bot/database.py',
        'run_web.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} - существует")
        else:
            print(f"   ❌ {file_path} - НЕ НАЙДЕН!")
    
    # 2. Проверяем импорты
    print("\n2. ПРОВЕРКА ИМПОРТОВ:")
    
    try:
        sys.path.append('.')
        from config.settings import config
        print("   ✅ config/settings.py - импортируется")
    except Exception as e:
        print(f"   ❌ config/settings.py - ошибка: {e}")
    
    try:
        from bot.database import Database
        print("   ✅ bot/database.py - импортируется")
    except Exception as e:
        print(f"   ❌ bot/database.py - ошибка: {e}")
    
    # 3. Проверяем веб-приложение
    print("\n3. ПРОВЕРКА ВЕБ-ПРИЛОЖЕНИЯ:")
    
    try:
        os.chdir('web')
        sys.path.append('..')
        from app import app
        print("   ✅ web/app.py - импортируется")
        print(f"   ✅ Flask app создан: {app}")
    except Exception as e:
        print(f"   ❌ web/app.py - ошибка: {e}")
    finally:
        os.chdir('..')
    
    # 4. Проверяем run_web.py
    print("\n4. ПРОВЕРКА run_web.py:")
    
    if os.path.exists('run_web.py'):
        try:
            with open('run_web.py', 'r') as f:
                content = f.read()
                print("   ✅ run_web.py - существует")
                print(f"   Содержимое: {content[:200]}...")
        except Exception as e:
            print(f"   ❌ run_web.py - ошибка чтения: {e}")
    else:
        print("   ❌ run_web.py - НЕ НАЙДЕН!")
    
    # 5. Проверяем зависимости
    print("\n5. ПРОВЕРКА ЗАВИСИМОСТЕЙ:")
    
    try:
        import flask
        print(f"   ✅ Flask: {flask.__version__}")
    except ImportError:
        print("   ❌ Flask не установлен")
    
    try:
        import requests
        print(f"   ✅ requests: {requests.__version__}")
    except ImportError:
        print("   ❌ requests не установлен")
    
    try:
        import sqlite3
        print("   ✅ sqlite3 доступен")
    except ImportError:
        print("   ❌ sqlite3 недоступен")

if __name__ == "__main__":
    debug_web_service() 