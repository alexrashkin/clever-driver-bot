#!/usr/bin/env python3
"""
Глубокая диагностика Telegram API
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def test_bot_permissions():
    """Проверяет права и настройки бота"""
    print("🤖 Проверка прав и настроек бота")
    print("=" * 40)
    
    # Проверяем getMe
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот активен: @{bot_info.get('username')}")
                print(f"📋 ID: {bot_info.get('id')}")
                print(f"📋 Имя: {bot_info.get('first_name')}")
                print(f"📋 Поддерживает inline: {bot_info.get('supports_inline_queries', False)}")
                print(f"📋 Может присоединяться к группам: {bot_info.get('can_join_groups', False)}")
                print(f"📋 Может читать групповые сообщения: {bot_info.get('can_read_all_group_messages', False)}")
                return True
            else:
                print(f"❌ API ошибка: {data.get('description')}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return False

def test_webhook_info():
    """Проверяет настройки webhook"""
    print(f"\n🔗 Проверка webhook настроек...")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data['result']
                print(f"📋 URL: {webhook_info.get('url', 'Не установлен')}")
                print(f"📋 Ожидает обновления: {webhook_info.get('pending_update_count', 0)}")
                print(f"📋 Последняя ошибка: {webhook_info.get('last_error_message', 'Нет')}")
                
                # Если webhook установлен, это может мешать getUpdates
                if webhook_info.get('url'):
                    print("⚠️ Webhook установлен - это может мешать getUpdates")
                    return True
                else:
                    print("✅ Webhook не установлен")
                    return False
            else:
                print(f"❌ API ошибка: {data.get('description')}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return False

def test_different_phone_formats():
    """Тестирует разные форматы номера телефона"""
    phone = "+79110930539"
    print(f"\n📱 Тестирование разных форматов номера {phone}")
    print("=" * 50)
    
    # Различные форматы номера
    formats = [
        phone,                    # +79110930539
        phone.replace("+", ""),   # 79110930539
        phone.replace("+7", ""),  # 9110930539
        phone.replace("+7", "7"), # 79110930539
        phone[1:],                # 79110930539 (без +)
        f"7{phone[1:]}",          # 79110930539
        f"8{phone[2:]}",          # 89110930539
    ]
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    
    for i, format_phone in enumerate(formats, 1):
        print(f"\n📤 Тест {i}: {format_phone}")
        
        data = {
            'chat_id': format_phone,
            'text': f'🔧 Тест формата {i}: {format_phone}'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            print(f"📡 HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Успешно!")
                    return format_phone
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
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return None

def test_get_chat_member():
    """Тестирует getChatMember для проверки доступа"""
    print(f"\n👤 Тестирование getChatMember...")
    
    # Сначала нужно получить chat_id из обновлений
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    params = {"limit": 1}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                if updates:
                    chat_id = updates[0]['message']['chat']['id']
                    print(f"📋 Найден chat_id: {chat_id}")
                    
                    # Тестируем getChatMember
                    member_url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getChatMember"
                    member_params = {"chat_id": chat_id, "user_id": chat_id}
                    
                    member_response = requests.get(member_url, params=member_params, timeout=10)
                    print(f"📡 getChatMember: HTTP {member_response.status_code}")
                    
                    if member_response.status_code == 200:
                        member_data = member_response.json()
                        if member_data.get('ok'):
                            member_info = member_data['result']
                            print(f"✅ Статус: {member_info.get('status')}")
                            print(f"📋 Пользователь: {member_info.get('user', {}).get('username', 'Нет')}")
                        else:
                            print(f"❌ API ошибка: {member_data.get('description')}")
                    else:
                        print(f"❌ HTTP {member_response.status_code}")
                else:
                    print("❌ Нет обновлений для тестирования")
            else:
                print(f"❌ API ошибка: {data.get('description')}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_privacy_settings():
    """Проверяет настройки приватности бота"""
    print(f"\n🔒 Проверка настроек приватности...")
    
    # Проверяем, может ли бот получать информацию о пользователях
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"📋 Бот: @{bot_info.get('username')}")
                print(f"📋 ID: {bot_info.get('id')}")
                
                # Проверяем, может ли бот отправлять сообщения
                print("\n💡 Возможные проблемы с приватностью:")
                print("1. Пользователь заблокировал бота")
                print("2. Настройки приватности запрещают получение сообщений")
                print("3. Пользователь не в сети или неактивен")
                print("4. Ограничения Telegram API для новых пользователей")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    print("🚀 Глубокая диагностика Telegram API")
    print("=" * 60)
    
    # Тест 1: Права бота
    if not test_bot_permissions():
        return
    
    # Тест 2: Webhook
    has_webhook = test_webhook_info()
    
    # Тест 3: Разные форматы номера
    working_format = test_different_phone_formats()
    
    # Тест 4: getChatMember
    test_get_chat_member()
    
    # Тест 5: Настройки приватности
    test_privacy_settings()
    
    print("\n" + "=" * 60)
    print("📋 Результаты диагностики:")
    
    if working_format:
        print(f"✅ Работающий формат найден: {working_format}")
        print("💡 Используйте этот формат для привязки")
    else:
        print("❌ Ни один формат номера не работает")
        print("💡 Возможные причины:")
        print("   - Пользователь заблокировал бота")
        print("   - Настройки приватности")
        print("   - Ограничения Telegram API")
        print("   - Пользователь не писал боту /start")
    
    if has_webhook:
        print("\n⚠️ Webhook установлен - это может мешать работе")
        print("💡 Рекомендация: отключите webhook для тестирования")
    
    print("\n🎯 Следующие шаги:")
    print("1. Попросите пользователя написать боту /start")
    print("2. Проверьте, не заблокирован ли бот")
    print("3. Попробуйте использовать username вместо номера")
    print("4. Проверьте настройки приватности в Telegram")

if __name__ == "__main__":
    main() 