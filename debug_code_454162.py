#!/usr/bin/env python3
"""
Детальная диагностика ошибки с кодом 454162
"""

import requests
import json
import sys
import os
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_454162.log', mode='w', encoding='utf-8')
    ]
)

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def test_telegram_api_detailed():
    """Детальное тестирование Telegram API"""
    print("🔍 Детальное тестирование Telegram API")
    print("=" * 50)
    
    # Запрашиваем контакт
    print("📝 Введите контакт, который вызывает ошибку HTTP 400:")
    contact = input("Контакт: ").strip()
    
    if not contact:
        print("❌ Контакт не указан")
        return
    
    print(f"\n🔍 Тестирование контакта: {contact}")
    
    # Определяем chat_id
    if contact.startswith('@'):
        username = contact[1:]
        chat_id = f"@{username}"
        print(f"📋 Username: {username}")
        print(f"📋 Chat ID: {chat_id}")
    elif contact.startswith('+'):
        chat_id = contact
        print(f"📋 Номер телефона: {contact}")
        print(f"📋 Chat ID: {chat_id}")
    else:
        chat_id = f"@{contact}"
        print(f"📋 Username (без @): {contact}")
        print(f"📋 Chat ID: {chat_id}")
    
    # Тестируем getMe
    print(f"\n🔍 Тестирование getMe...")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        print(f"📡 GET /getMe: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот активен: @{bot_info.get('username')}")
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Тестируем getChat (если это номер телефона)
    if contact.startswith('+'):
        print(f"\n🔍 Тестирование getChat для номера {contact}...")
        check_url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getChat"
        check_params = {"chat_id": contact}
        
        try:
            check_response = requests.get(check_url, params=check_params, timeout=10)
            print(f"📡 GET /getChat: HTTP {check_response.status_code}")
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                if check_data.get('ok'):
                    chat_info = check_data['result']
                    print(f"✅ Чат найден: {chat_info.get('type')} - {chat_info.get('title', chat_info.get('first_name', 'Unknown'))}")
                    chat_id = chat_info['id']
                    print(f"📋 Получен chat_id: {chat_id}")
                else:
                    error_desc = check_data.get('description', 'Неизвестная ошибка')
                    print(f"❌ getChat ошибка: {error_desc}")
            else:
                print(f"❌ getChat HTTP ошибка: {check_response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка getChat: {e}")
    
    # Тестируем sendMessage с разными вариантами
    print(f"\n🔍 Тестирование sendMessage...")
    
    test_messages = [
        {
            'name': 'Простое сообщение',
            'data': {
                'chat_id': chat_id,
                'text': 'Тестовое сообщение'
            }
        },
        {
            'name': 'Сообщение с эмодзи',
            'data': {
                'chat_id': chat_id,
                'text': '🔧 Тестовое сообщение'
            }
        },
        {
            'name': 'Сообщение с кодом',
            'data': {
                'chat_id': chat_id,
                'text': f'Код подтверждения: 454162'
            }
        }
    ]
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    
    for i, test in enumerate(test_messages, 1):
        print(f"\n📤 Тест {i}: {test['name']}")
        print(f"📋 Данные: {json.dumps(test['data'], ensure_ascii=False)}")
        
        try:
            response = requests.post(url, json=test['data'], timeout=10)
            print(f"📡 POST /sendMessage: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Сообщение отправлено успешно!")
                    message_id = result['result']['message_id']
                    print(f"📋 ID сообщения: {message_id}")
                else:
                    error_msg = result.get('description', 'Неизвестная ошибка')
                    print(f"❌ API ошибка: {error_msg}")
            elif response.status_code == 400:
                print("❌ HTTP 400 - Bad Request")
                try:
                    error_data = response.json()
                    print(f"📋 Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    
                    error_msg = error_data.get('description', '')
                    if "chat not found" in error_msg.lower():
                        print("\n📋 Решение:")
                        print("1. Убедитесь, что пользователь существует в Telegram")
                        print("2. Проверьте правильность username или номера телефона")
                        print("3. Попросите пользователя написать боту /start")
                    elif "forbidden" in error_msg.lower():
                        print("\n📋 Решение:")
                        print("1. Пользователь заблокировал бота")
                        print("2. Попросите пользователя разблокировать бота")
                        print("3. Попросите написать боту /start")
                    elif "chat_id is empty" in error_msg.lower():
                        print("\n📋 Решение:")
                        print("1. Проверьте формат контакта")
                        print("2. Используйте @username или +7XXXXXXXXXX")
                        
                except:
                    print(f"📋 Текст ответа: {response.text}")
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"📋 Текст ответа: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")

def main():
    print("🚀 Детальная диагностика ошибки HTTP 400")
    print("=" * 60)
    
    # Проверяем конфигурацию
    print(f"🤖 Бот: @{config.TELEGRAM_BOT_USERNAME}")
    print(f"🔑 Токен: {config.TELEGRAM_TOKEN[:10]}...")
    print(f"📁 Логи сохраняются в: debug_454162.log")
    
    # Запускаем детальное тестирование
    test_telegram_api_detailed()
    
    print("\n" + "=" * 60)
    print("📋 Проверьте файл debug_454162.log для детальных логов")

if __name__ == "__main__":
    main() 