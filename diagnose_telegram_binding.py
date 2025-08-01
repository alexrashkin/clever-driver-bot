#!/usr/bin/env python3
"""
Диагностический скрипт для тестирования привязки Telegram аккаунта
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def test_telegram_api():
    """Тестирует доступность Telegram Bot API"""
    print("🔍 Тестирование Telegram Bot API...")
    
    # Проверяем токен
    if not config.TELEGRAM_TOKEN:
        print("❌ Токен Telegram бота не настроен")
        return False
    
    print(f"✅ Токен найден: {config.TELEGRAM_TOKEN[:10]}...")
    
    # Тестируем getMe
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        print(f"📡 GET /getMe: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот активен: @{bot_info.get('username')} ({bot_info.get('first_name')})")
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_send_message(chat_id):
    """Тестирует отправку сообщения"""
    print(f"\n📤 Тестирование отправки сообщения в {chat_id}...")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': '🔧 Тестовое сообщение для диагностики привязки аккаунта',
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"📡 POST /sendMessage: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Сообщение отправлено успешно")
                return True
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                print(f"❌ Ошибка отправки: {error_msg}")
                return False
        else:
            print(f"❌ HTTP ошибка {response.status_code}")
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    print(f"📋 Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📋 Текст ответа: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_get_chat(chat_id):
    """Тестирует получение информации о чате"""
    print(f"\n🔍 Тестирование получения информации о чате {chat_id}...")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getChat"
    params = {"chat_id": chat_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 GET /getChat: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                chat_info = result['result']
                print(f"✅ Чат найден: {chat_info.get('type')} - {chat_info.get('title', chat_info.get('first_name', 'Unknown'))}")
                return True
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                print(f"❌ Ошибка получения чата: {error_msg}")
                return False
        else:
            print(f"❌ HTTP ошибка {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def main():
    print("🚀 Диагностика привязки Telegram аккаунта")
    print("=" * 50)
    
    # Тестируем API
    if not test_telegram_api():
        print("\n❌ Telegram Bot API недоступен. Проверьте токен и интернет-соединение.")
        return
    
    # Запрашиваем тестовый контакт
    print("\n📝 Введите тестовый контакт для диагностики:")
    print("Варианты:")
    print("1. Username: @username")
    print("2. Номер телефона: +79001234567")
    print("3. Просто username: username")
    
    contact = input("Введите контакт: ").strip()
    
    if not contact:
        print("❌ Контакт не указан")
        return
    
    # Определяем тип контакта
    if contact.startswith('@'):
        username = contact[1:]
        chat_id = f"@{username}"
        print(f"📋 Определен как username: @{username}")
    elif contact.startswith('+'):
        phone = contact
        chat_id = phone
        print(f"📋 Определен как номер телефона: {phone}")
    else:
        username = contact
        chat_id = f"@{username}"
        print(f"📋 Определен как username: @{username}")
    
    # Тестируем getChat (если это номер телефона)
    if contact.startswith('+'):
        test_get_chat(chat_id)
    
    # Тестируем отправку сообщения
    test_send_message(chat_id)
    
    print("\n" + "=" * 50)
    print("📋 Рекомендации:")
    print("1. Убедитесь, что пользователь существует в Telegram")
    print("2. Убедитесь, что пользователь не заблокировал бота")
    print("3. Для username: убедитесь, что формат правильный (@username)")
    print("4. Для номера: убедитесь, что номер указан в международном формате")
    print("5. Попросите пользователя написать боту /start")

if __name__ == "__main__":
    main() 