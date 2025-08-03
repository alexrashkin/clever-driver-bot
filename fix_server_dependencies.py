#!/usr/bin/env python3
"""
Исправление зависимостей на сервере
"""

import subprocess
import sys
import os

def install_dependencies():
    """Устанавливаем зависимости"""
    print("🔧 Установка зависимостей...")
    
    dependencies = [
        'python-dotenv',
        'requests',
        'flask'
    ]
    
    for dep in dependencies:
        print(f"📦 Установка {dep}...")
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {dep} установлен")
            else:
                print(f"❌ Ошибка установки {dep}: {result.stderr}")
        except Exception as e:
            print(f"❌ Ошибка при установке {dep}: {e}")

def test_imports():
    """Тестируем импорты"""
    print("\n🧪 Тестирование импортов...")
    
    try:
        import dotenv
        print("✅ python-dotenv импортируется")
    except ImportError:
        print("❌ python-dotenv не импортируется")
    
    try:
        import requests
        print("✅ requests импортируется")
    except ImportError:
        print("❌ requests не импортируется")
    
    try:
        import flask
        print("✅ flask импортируется")
    except ImportError:
        print("❌ flask не импортируется")

def test_web_app():
    """Тестируем веб-приложение"""
    print("\n🌐 Тестирование веб-приложения...")
    
    try:
        # Добавляем пути
        current_dir = os.path.dirname(os.path.abspath(__file__))
        web_dir = os.path.join(current_dir, 'web')
        
        sys.path.insert(0, current_dir)
        sys.path.insert(0, web_dir)
        
        from bot.database import Database
        print("✅ Database импортируется")
        
        db = Database()
        users = db.get_all_users()
        
        receiver = None
        for user in users:
            if user.get('login') == 'receiver':
                receiver = user
                break
        
        if receiver:
            print(f"✅ Пользователь receiver найден")
            print(f"  Email: {receiver.get('email')}")
        else:
            print("❌ Пользователь receiver не найден")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Исправление зависимостей на сервере")
    print("=" * 60)
    
    install_dependencies()
    test_imports()
    test_web_app()
    
    print("\n🎯 Исправление завершено!") 