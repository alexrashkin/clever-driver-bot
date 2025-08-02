#!/usr/bin/env python3
"""
Проверка истории бота и поиск активных пользователей
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
    print("🤖 Информация о боте")
    print("=" * 30)
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот активен: @{bot_info.get('username')}")
                print(f"📋 ID бота: {bot_info.get('id')}")
                print(f"📋 Имя: {bot_info.get('first_name')}")
                print(f"📋 Can join groups: {bot_info.get('can_join_groups', False)}")
                print(f"📋 Can read all group messages: {bot_info.get('can_read_all_group_messages', False)}")
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return False

def get_all_updates():
    """Получает все доступные обновления"""
    print(f"\n📋 Получение всех обновлений...")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    params = {"limit": 100, "offset": -1}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 GET /getUpdates: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                print(f"📋 Всего обновлений: {len(updates)}")
                
                if len(updates) == 0:
                    print("❌ История бота пуста")
                    print("💡 Возможные причины:")
                    print("   - Бот новый и никто не писал")
                    print("   - История была очищена")
                    print("   - Вы писали с другого аккаунта")
                    return []
                
                # Группируем по пользователям
                users = {}
                for update in updates:
                    if 'message' in update:
                        message = update['message']
                        user = message.get('from', {})
                        user_id = user.get('id')
                        
                        if user_id not in users:
                            users[user_id] = {
                                'id': user_id,
                                'username': user.get('username'),
                                'first_name': user.get('first_name'),
                                'last_name': user.get('last_name'),
                                'messages': []
                            }
                        
                        users[user_id]['messages'].append({
                            'text': message.get('text', ''),
                            'date': message.get('date', 0)
                        })
                
                print(f"\n👥 Найдено пользователей: {len(users)}")
                for user_id, user_info in users.items():
                    print(f"\n📱 Пользователь {user_id}:")
                    print(f"   Username: @{user_info['username'] or 'Нет'}")
                    print(f"   Имя: {user_info['first_name'] or 'Нет'}")
                    print(f"   Фамилия: {user_info['last_name'] or 'Нет'}")
                    print(f"   Сообщений: {len(user_info['messages'])}")
                    
                    # Показываем последние сообщения
                    recent_messages = user_info['messages'][-3:]  # Последние 3
                    for msg in recent_messages:
                        print(f"   - {msg['text']}")
                
                return list(users.keys())
            else:
                print(f"❌ API ошибка: {data.get('description')}")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return []

def test_send_to_user(user_id):
    """Тестирует отправку сообщения конкретному пользователю"""
    print(f"\n📤 Тест отправки пользователю {user_id}")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': user_id,
        'text': '🔧 Тест привязки аккаунта - проверка связи'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"📡 HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Сообщение отправлено успешно!")
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
    print("🚀 Проверка истории бота и активных пользователей")
    print("=" * 60)
    
    # Проверяем информацию о боте
    if not check_bot_info():
        return
    
    # Получаем всех пользователей
    user_ids = get_all_updates()
    
    if user_ids:
        print(f"\n🔍 Тестирование отправки активным пользователям...")
        for user_id in user_ids:
            test_send_to_user(user_id)
    
    print("\n" + "=" * 60)
    print("📋 Выводы:")
    if len(user_ids) == 0:
        print("❌ В истории бота нет пользователей")
        print("💡 Это означает, что:")
        print("   1. Вы писали боту с другого аккаунта")
        print("   2. История была очищена")
        print("   3. Номер телефона в Telegram отличается")
    else:
        print(f"✅ Найдено {len(user_ids)} активных пользователей")
        print("💡 Попробуйте привязать аккаунт используя username одного из них")
    
    print("\n🎯 Рекомендации:")
    print("1. Проверьте, с какого аккаунта вы писали боту")
    print("2. Убедитесь, что номер +79110930539 привязан к правильному Telegram")
    print("3. Попробуйте использовать username вместо номера")
    print("4. Напишите боту /start снова с нужного аккаунта")

if __name__ == "__main__":
    main() 