#!/usr/bin/env python3
"""
Поиск правильного Telegram аккаунта
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def test_username_variants():
    """Тестирует различные варианты username"""
    print("🔍 Поиск правильного username")
    print("=" * 40)
    
    # Различные варианты username
    username_variants = [
        "alexrashkin",
        "alex_rashkin", 
        "alex.rashkin",
        "rashkin",
        "alex",
        "alexander",
        "alexandr"
    ]
    
    working_usernames = []
    
    for username in username_variants:
        print(f"\n🔍 Тестирование: @{username}")
        
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': f"@{username}",
            'text': f'🔧 Тест связи для @{username}'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Сообщение отправлено!")
                    working_usernames.append(f"@{username}")
                else:
                    error_msg = result.get('description', 'Неизвестная ошибка')
                    print(f"❌ API ошибка: {error_msg}")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('description', '')
                    if "chat not found" in error_msg.lower():
                        print("❌ Пользователь не найден")
                    else:
                        print(f"❌ Ошибка: {error_msg}")
                except:
                    print("❌ HTTP 400 - Bad Request")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return working_usernames

def test_phone_variants():
    """Тестирует различные варианты номера телефона"""
    print(f"\n📱 Поиск правильного номера телефона")
    print("=" * 40)
    
    # Различные варианты номера
    phone_variants = [
        "+79110930539",
        "79110930539",
        "89110930539",
        "+7 911 093 05 39",
        "+7-911-093-05-39",
        "9110930539"
    ]
    
    working_phones = []
    
    for phone in phone_variants:
        print(f"\n🔍 Тестирование: {phone}")
        
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': phone,
            'text': f'🔧 Тест связи для {phone}'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Сообщение отправлено!")
                    working_phones.append(phone)
                else:
                    error_msg = result.get('description', 'Неизвестная ошибка')
                    print(f"❌ API ошибка: {error_msg}")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('description', '')
                    if "chat not found" in error_msg.lower():
                        print("❌ Пользователь не найден")
                    else:
                        print(f"❌ Ошибка: {error_msg}")
                except:
                    print("❌ HTTP 400 - Bad Request")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return working_phones

def main():
    print("🚀 Поиск правильного Telegram аккаунта")
    print("=" * 60)
    print("📋 Этот скрипт проверит различные варианты username и номера")
    print("💡 Если найдется работающий контакт, используйте его для привязки")
    print("=" * 60)
    
    # Тестируем username
    working_usernames = test_username_variants()
    
    # Тестируем номера телефонов
    working_phones = test_phone_variants()
    
    print("\n" + "=" * 60)
    print("📋 Результаты поиска:")
    
    if working_usernames:
        print(f"✅ Работающие username: {', '.join(working_usernames)}")
    else:
        print("❌ Работающих username не найдено")
    
    if working_phones:
        print(f"✅ Работающие номера: {', '.join(working_phones)}")
    else:
        print("❌ Работающих номеров не найдено")
    
    if not working_usernames and not working_phones:
        print("\n💡 Ни один контакт не работает")
        print("🎯 Рекомендации:")
        print("1. Убедитесь, что вы писали боту /start")
        print("2. Проверьте, не заблокирован ли бот")
        print("3. Проверьте настройки приватности в Telegram")
        print("4. Попробуйте создать новый username")
        print("5. Убедитесь, что номер телефона привязан к правильному аккаунту")
    else:
        print("\n✅ Найдены работающие контакты!")
        print("💡 Используйте любой из них для привязки аккаунта")

if __name__ == "__main__":
    main() 