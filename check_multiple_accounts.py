#!/usr/bin/env python3
"""
Проверка нескольких возможных аккаунтов
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def test_common_usernames():
    """Тестирует распространенные варианты username"""
    print("🔍 Проверка распространенных username")
    print("=" * 50)
    
    # Распространенные варианты username
    usernames = [
        "alexrashkin",
        "alex_rashkin",
        "alex.rashkin", 
        "rashkin",
        "alex",
        "alexander",
        "alexandr",
        "rashkin_alex",
        "alex_r",
        "rashkin_a"
    ]
    
    working_usernames = []
    
    for username in usernames:
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
            elif response.status_code == 403:
                print("⚠️ Пользователь заблокировал бота")
                working_usernames.append(f"@{username} (заблокирован)")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return working_usernames

def test_phone_variants():
    """Тестирует различные варианты номера телефона"""
    print(f"\n📱 Проверка вариантов номера телефона")
    print("=" * 50)
    
    # Различные варианты номера
    phones = [
        "+79110930539",
        "79110930539", 
        "89110930539",
        "+7 911 093 05 39",
        "+7-911-093-05-39",
        "9110930539",
        "+79110930539",
        "79110930539"
    ]
    
    working_phones = []
    
    for phone in phones:
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
            elif response.status_code == 403:
                print("⚠️ Пользователь заблокировал бота")
                working_phones.append(f"{phone} (заблокирован)")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return working_phones

def main():
    print("🚀 Проверка нескольких возможных аккаунтов")
    print("=" * 60)
    print("📋 Этот скрипт проверит различные варианты username и номера")
    print("💡 Если найдется работающий контакт, используйте его для привязки")
    print("=" * 60)
    
    # Тестируем username
    working_usernames = test_common_usernames()
    
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
        print("1. Проверьте, что вы писали боту с правильного аккаунта")
        print("2. Убедитесь, что номер +79110930539 привязан к правильному Telegram")
        print("3. Проверьте, не заблокирован ли бот")
        print("4. Попробуйте создать новый username")
        print("5. Проверьте, что используете правильный бот")
    else:
        print("\n✅ Найдены работающие контакты!")
        print("💡 Используйте любой из них для привязки аккаунта")
        
        if any("заблокирован" in contact for contact in working_usernames + working_phones):
            print("\n⚠️ Обнаружены заблокированные контакты!")
            print("💡 Разблокируйте бота в настройках Telegram")

if __name__ == "__main__":
    main() 