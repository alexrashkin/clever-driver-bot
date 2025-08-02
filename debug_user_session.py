#!/usr/bin/env python3
"""
Диагностика сессии пользователя и проверка разных способов отправки
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def test_different_chat_ids():
    """Тестирует разные варианты chat_id для номера +79110930539"""
    phone = "+79110930539"
    print(f"🔍 Тестирование разных вариантов chat_id для {phone}")
    
    # Варианты chat_id для тестирования
    chat_id_variants = [
        phone,                    # +79110930539
        phone.replace("+", ""),   # 79110930539
        phone.replace("+7", ""),  # 9110930539
        phone.replace("+7", "7"), # 79110930539
        f"@{phone}",              # @+79110930539
        phone[1:],                # 79110930539 (без +)
    ]
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    
    for i, chat_id in enumerate(chat_id_variants, 1):
        print(f"\n📤 Тест {i}: chat_id = '{chat_id}'")
        
        data = {
            'chat_id': chat_id,
            'text': f'🔧 Тест {i}: Проверка привязки аккаунта'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            print(f"📡 HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Успешно!")
                    message_id = result['result']['message_id']
                    print(f"📋 ID сообщения: {message_id}")
                    return chat_id
                else:
                    error_msg = result.get('description', 'Неизвестная ошибка')
                    print(f"❌ API ошибка: {error_msg}")
            elif response.status_code == 400:
                print("❌ HTTP 400 - Bad Request")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('description', '')
                    print(f"📋 Ошибка: {error_msg}")
                except:
                    print(f"📋 Текст: {response.text}")
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"📋 Текст: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return None

def test_get_updates():
    """Проверяет последние обновления бота"""
    print(f"\n🔍 Проверка последних обновлений бота...")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    params = {"limit": 10}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 GET /getUpdates: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                print(f"📋 Найдено обновлений: {len(updates)}")
                
                for i, update in enumerate(updates):
                    if 'message' in update:
                        message = update['message']
                        chat = message.get('chat', {})
                        user = message.get('from', {})
                        
                        print(f"\n📱 Обновление {i+1}:")
                        print(f"   Chat ID: {chat.get('id')}")
                        print(f"   Chat Type: {chat.get('type')}")
                        print(f"   User ID: {user.get('id')}")
                        print(f"   Username: @{user.get('username', 'Нет')}")
                        print(f"   First Name: {user.get('first_name', 'Нет')}")
                        print(f"   Text: {message.get('text', 'Нет текста')}")
                        
                        # Проверяем, есть ли пользователь с номером +79110930539
                        if user.get('id'):
                            return user.get('id')
            else:
                print(f"❌ API ошибка: {data.get('description')}")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return None

def test_with_user_id(user_id):
    """Тестирует отправку по user_id"""
    if not user_id:
        return False
    
    print(f"\n🔍 Тестирование отправки по user_id: {user_id}")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': user_id,
        'text': '🔧 Тест отправки по user_id'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"📡 HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Успешно отправлено по user_id!")
                return True
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                print(f"❌ API ошибка: {error_msg}")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return False

def main():
    print("🚀 Диагностика сессии пользователя")
    print("=" * 50)
    
    # Тест 1: Разные варианты chat_id
    working_chat_id = test_different_chat_ids()
    
    if working_chat_id:
        print(f"\n✅ Работающий chat_id найден: {working_chat_id}")
        return
    
    # Тест 2: Проверка обновлений
    user_id = test_get_updates()
    
    if user_id:
        # Тест 3: Отправка по user_id
        test_with_user_id(user_id)
    
    print("\n" + "=" * 50)
    print("📋 Возможные причины проблемы:")
    print("1. Номер телефона не совпадает с аккаунтом в Telegram")
    print("2. Пользователь заблокировал бота")
    print("3. Сессия пользователя истекла")
    print("4. Проблемы с форматом номера телефона")
    
    print("\n💡 Рекомендации:")
    print("1. Проверьте, что номер +79110930539 привязан к Telegram")
    print("2. Попробуйте написать боту /start снова")
    print("3. Используйте username вместо номера телефона")
    print("4. Проверьте, не заблокирован ли бот")

if __name__ == "__main__":
    main() 