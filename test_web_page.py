#!/usr/bin/env python3
"""
Тест конкретной страницы веб-приложения
"""

import requests
import sys

def test_web_page():
    """Тестирует конкретную страницу веб-приложения"""
    
    base_url = "http://127.0.0.1:5000"
    
    try:
        print("=== ТЕСТ ВЕБ-СТРАНИЦЫ ===")
        
        # Тест 1: Главная страница
        print("\n1. Тестируем главную страницу...")
        try:
            response = requests.get(base_url, timeout=10)
            print(f"   Статус: {response.status_code}")
            print(f"   Успешно: {response.status_code == 200}")
            
            if response.status_code != 200:
                print(f"   Ошибка: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Тест 2: Страница входа
        print("\n2. Тестируем страницу входа...")
        try:
            response = requests.get(f"{base_url}/login", timeout=10)
            print(f"   Статус: {response.status_code}")
            print(f"   Успешно: {response.status_code == 200}")
            
            if response.status_code != 200:
                print(f"   Ошибка: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Тест 3: Страница привязки (должна вернуть 302 или 200)
        print("\n3. Тестируем страницу привязки...")
        try:
            response = requests.get(f"{base_url}/bind_telegram_form", timeout=10, allow_redirects=False)
            print(f"   Статус: {response.status_code}")
            print(f"   Редирект: {response.status_code in [302, 301]}")
            print(f"   Успешно: {response.status_code in [200, 302, 301]}")
            
            if response.status_code not in [200, 302, 301]:
                print(f"   Ошибка: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")

if __name__ == "__main__":
    test_web_page() 