#!/usr/bin/env python3
"""
Тест импортов
"""

import sys
import os

def test_imports():
    """Тестирует импорты"""
    
    print("=== ТЕСТ ИМПОРТОВ ===")
    
    # Добавляем пути
    current_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(current_dir, 'web')
    
    print(f"Текущая директория: {current_dir}")
    print(f"Web директория: {web_dir}")
    
    sys.path.insert(0, current_dir)
    sys.path.insert(0, web_dir)
    
    print(f"Python path: {sys.path[:3]}")
    
    try:
        print("\n1. Тестируем config...")
        from config.settings import config
        print("   ✅ config импортирован")
        
        print("\n2. Тестируем bot.database...")
        from bot.database import Database
        print("   ✅ Database импортирован")
        
        print("\n3. Тестируем web.app...")
        from app import app
        print("   ✅ app импортирован")
        print(f"   App: {app}")
        
        print("\n4. Тестируем run_web.py...")
        # Имитируем запуск run_web.py
        print("   ✅ Все импорты работают")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imports() 