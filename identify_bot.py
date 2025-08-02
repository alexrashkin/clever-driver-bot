#!/usr/bin/env python3
"""
Идентификация бота, который отвечает пользователю
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def check_bot_identity():
    """Проверяет идентичность бота"""
    print("🤖 Проверка идентичности бота")
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
                
                print(f"\n🔍 Проверьте, что это тот же бот, который отвечает вам:")
                print(f"📱 Username: @{bot.get('username', 'Нет')}")
                print(f"📋 Имя: {bot.get('first_name', 'Нет')}")
                
                return bot
            else:
                print(f"❌ API ошибка: {result.get('description', 'Неизвестная ошибка')}")
                return None
        else:
            print(f"❌ HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def test_webhook_status():
    """Проверяет статус webhook"""
    print(f"\n🔗 Проверка webhook статуса")
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
                    print("⚠️ Webhook установлен - обновления могут приходить через него")
                    return True
                else:
                    print("✅ Webhook не установлен - используется polling")
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

def clear_updates():
    """Очищает обновления"""
    print(f"\n🗑️ Очистка обновлений")
    print("=" * 40)
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    params = {'offset': -1}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Обновления очищены")
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

def wait_for_new_message():
    """Ждет новое сообщение"""
    print(f"\n⏳ Ожидание нового сообщения")
    print("=" * 40)
    print("📱 Напишите боту любое сообщение прямо сейчас")
    print("⏰ Ожидание 10 секунд...")
    
    import time
    time.sleep(10)
    
    # Проверяем обновления
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                updates = result.get('result', [])
                print(f"📋 Найдено обновлений: {len(updates)}")
                
                if updates:
                    print("✅ Новые обновления найдены!")
                    for update in updates:
                        if 'message' in update:
                            message = update['message']
                            user = message.get('from', {})
                            chat = message.get('chat', {})
                            
                            print(f"👤 Пользователь: {user.get('first_name', '')} {user.get('last_name', '')}")
                            print(f"📱 Username: @{user.get('username', 'Нет')}")
                            print(f"🆔 ID: {user.get('id', 'Нет')}")
                            print(f"💬 Сообщение: {message.get('text', 'Нет текста')}")
                            print(f"📅 Дата: {message.get('date', 'Нет')}")
                            print("-" * 40)
                            
                            return user.get('username', ''), user.get('id', '')
                else:
                    print("❌ Новых обновлений не найдено")
                    return None, None
            else:
                print(f"❌ API ошибка: {result.get('description', 'Неизвестная ошибка')}")
                return None, None
        else:
            print(f"❌ HTTP {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None

def main():
    print("🚀 Идентификация бота")
    print("=" * 60)
    
    # Проверяем идентичность бота
    bot = check_bot_identity()
    if not bot:
        print("❌ Не удалось получить информацию о боте")
        return
    
    # Проверяем webhook
    has_webhook = test_webhook_status()
    
    # Очищаем обновления
    clear_updates()
    
    # Ждем новое сообщение
    username, user_id = wait_for_new_message()
    
    print("\n" + "=" * 60)
    print("📋 Результаты:")
    
    if username and user_id:
        print(f"✅ Связь установлена!")
        print(f"👤 Ваш username: @{username}")
        print(f"🆔 Ваш ID: {user_id}")
        print(f"🤖 Бот: @{bot.get('username', 'Нет')}")
        
        print("\n💡 Теперь попробуйте привязать аккаунт:")
        print(f"1. Используйте username: @{username}")
        print(f"2. Или используйте ID: {user_id}")
    else:
        print("❌ Связь не установлена")
        print("💡 Возможные причины:")
        print("   - Вы не написали сообщение боту")
        print("   - Проблемы с сетью")
        print("   - Бот использует webhook")
        
        print("\n🎯 Рекомендации:")
        print("1. Напишите боту любое сообщение")
        print("2. Запустите скрипт снова")
        print("3. Проверьте, что используете правильный бот")

if __name__ == "__main__":
    main() 