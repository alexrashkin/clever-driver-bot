#!/usr/bin/env python3
"""
Принудительная привязка аккаунта
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def force_send_message():
    """Принудительная отправка сообщения"""
    print("🔧 Принудительная отправка сообщения")
    print("=" * 50)
    
    # Пробуем разные варианты
    test_contacts = [
        "@alexrashkin",
        "+79110930539",
        "alexrashkin"  # без @
    ]
    
    for contact in test_contacts:
        print(f"\n📤 Тестирование: {contact}")
        
        # Определяем chat_id
        if contact.startswith('@'):
            chat_id = contact
        elif contact.startswith('+'):
            chat_id = contact
        else:
            chat_id = f"@{contact}"
        
        print(f"📋 Используемый chat_id: {chat_id}")
        
        # Отправляем сообщение
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': '🔧 Принудительный тест связи - если вы получили это сообщение, привязка должна работать!'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            print(f"📡 HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Сообщение отправлено!")
                    message_id = result['result']['message_id']
                    print(f"📋 ID сообщения: {message_id}")
                    print(f"🎯 Контакт {contact} работает!")
                    return contact
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

def check_privacy_settings():
    """Проверяет настройки приватности"""
    print(f"\n🔒 Проверка настроек приватности")
    print("=" * 50)
    print("📋 Возможные проблемы с приватностью:")
    print("1. Пользователь не писал боту /start")
    print("2. Настройки приватности блокируют сообщения")
    print("3. Пользователь заблокировал бота")
    print("4. Ограничения Telegram API")
    
    print("\n🎯 Рекомендации:")
    print("1. Напишите боту /start с мобильного приложения")
    print("2. Проверьте настройки приватности в Telegram")
    print("3. Убедитесь, что бот не заблокирован")
    print("4. Попробуйте создать новый username")

def main():
    print("🚀 Принудительная привязка аккаунта")
    print("=" * 60)
    
    # Принудительная отправка
    working_contact = force_send_message()
    
    if working_contact:
        print(f"\n✅ Работающий контакт найден: {working_contact}")
        print("💡 Используйте этот контакт для привязки аккаунта")
        print("\n🎯 Следующие шаги:")
        print("1. Авторизуйтесь в веб-интерфейсе")
        print("2. Перейдите на страницу привязки")
        print(f"3. Используйте контакт: {working_contact}")
    else:
        print("\n❌ Ни один контакт не работает")
        check_privacy_settings()
        
        print("\n🔧 Альтернативное решение:")
        print("1. Откройте мобильное приложение Telegram")
        print("2. Найдите бота: @Clever_driver_bot")
        print("3. Напишите: /start")
        print("4. Дождитесь ответа от бота")
        print("5. Попробуйте привязать аккаунт снова")

if __name__ == "__main__":
    main() 