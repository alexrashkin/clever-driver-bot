#!/usr/bin/env python3
"""
Проверка настроек бота и возможных проблем
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def check_bot_info():
    """Проверяет информацию о боте"""
    print("🤖 Проверка информации о боте")
    print("=" * 40)
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot = result['result']
                print(f"✅ Бот активен: @{bot.get('username', 'Нет')}")
                print(f"📋 ID: {bot.get('id', 'Нет')}")
                print(f"📋 Имя: {bot.get('first_name', 'Нет')}")
                print(f"📋 Поддерживает inline: {bot.get('can_join_groups', False)}")
                print(f"📋 Может читать групповые сообщения: {bot.get('can_read_all_group_messages', False)}")
                return True
            else:
                print(f"❌ API ошибка: {result.get('description', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_webhook():
    """Проверяет настройки webhook"""
    print(f"\n🔗 Проверка webhook настроек")
    print("=" * 40)
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                webhook = result['result']
                print(f"📋 URL: {webhook.get('url', 'Не установлен')}")
                print(f"📋 Ожидает обновления: {webhook.get('pending_update_count', 0)}")
                print(f"📋 Последняя ошибка: {webhook.get('last_error_message', 'Нет')}")
                
                if webhook.get('url'):
                    print("⚠️ Webhook установлен - это может мешать получению обновлений")
                    return True
                else:
                    print("✅ Webhook не установлен - бот использует polling")
                    return False
            else:
                print(f"❌ API ошибка: {result.get('description', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def delete_webhook():
    """Удаляет webhook если он установлен"""
    print(f"\n🗑️ Удаление webhook (если установлен)")
    print("=" * 40)
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/deleteWebhook"
    
    try:
        response = requests.post(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook удален")
                return True
            else:
                print(f"❌ API ошибка: {result.get('description', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_direct_message():
    """Тестирует прямую отправку сообщения"""
    print(f"\n📤 Тест прямой отправки сообщения")
    print("=" * 40)
    
    # Пробуем отправить сообщение напрямую
    test_contacts = [
        "@alexrashkin",
        "+79110930539"
    ]
    
    for contact in test_contacts:
        print(f"\n🔍 Тестирование: {contact}")
        
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': contact,
            'text': '🔧 Тест связи - если вы получили это сообщение, связь работает!'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            print(f"📡 HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Сообщение отправлено!")
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
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return None

def main():
    print("🚀 Проверка настроек бота")
    print("=" * 60)
    
    # Проверяем информацию о боте
    if not check_bot_info():
        print("❌ Не удалось получить информацию о боте")
        return
    
    # Проверяем webhook
    has_webhook = check_webhook()
    
    # Если есть webhook, удаляем его
    if has_webhook:
        delete_webhook()
    
    # Тестируем прямую отправку
    working_contact = test_direct_message()
    
    print("\n" + "=" * 60)
    print("📋 Результаты:")
    
    if working_contact:
        print(f"✅ Связь работает с контактом: {working_contact}")
        print("💡 Теперь попробуйте привязать аккаунт через веб-интерфейс")
    else:
        print("❌ Связь не работает")
        print("💡 Возможные причины:")
        print("   - Пользователь не писал боту /start")
        print("   - Настройки приватности блокируют сообщения")
        print("   - Пользователь заблокировал бота")
        print("   - Проблемы с Telegram API")
        
        print("\n🎯 Рекомендации:")
        print("1. Напишите боту /start с мобильного приложения")
        print("2. Проверьте настройки приватности в Telegram")
        print("3. Убедитесь, что бот не заблокирован")
        print("4. Попробуйте создать новый username")

if __name__ == "__main__":
    main() 