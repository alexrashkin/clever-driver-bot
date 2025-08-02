#!/usr/bin/env python3
"""
Быстрый тест для проверки конкретного контакта
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def quick_test(contact):
    """Быстрый тест контакта"""
    print(f"🔍 Быстрый тест контакта: {contact}")
    
    # Определяем chat_id
    if contact.startswith('@'):
        username = contact[1:]
        chat_id = f"@{username}"
    elif contact.startswith('+'):
        chat_id = contact
    else:
        chat_id = f"@{contact}"
    
    print(f"📋 Chat ID: {chat_id}")
    
    # Тестируем sendMessage
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': '🔧 Тест привязки аккаунта'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"📡 HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Успешно!")
                return True
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                print(f"❌ API ошибка: {error_msg}")
                return False
        elif response.status_code == 400:
            print("❌ HTTP 400 - Bad Request")
            try:
                error_data = response.json()
                error_msg = error_data.get('description', '')
                print(f"📋 Ошибка: {error_msg}")
            except:
                print(f"📋 Текст: {response.text}")
            return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🚀 Быстрый тест контакта")
    print("=" * 30)
    
    # Запрашиваем контакт
    contact = input("Введите контакт: ").strip()
    
    if not contact:
        print("❌ Контакт не указан")
        return
    
    # Тестируем
    success = quick_test(contact)
    
    if success:
        print("\n✅ Контакт работает! Привязка должна функционировать.")
    else:
        print("\n❌ Контакт не работает. Проверьте:")
        print("1. Правильность username/номера")
        print("2. Существование пользователя в Telegram")
        print("3. Наличие диалога с ботом (/start)")

if __name__ == "__main__":
    main() 