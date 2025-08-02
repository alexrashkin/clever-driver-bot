#!/usr/bin/env python3
"""
Скрипт для установки связи с ботом
"""

import requests
import json
import sys
import os
import time

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def wait_for_user_message():
    """Ждет сообщение от пользователя"""
    print("🤖 Ожидание сообщения от пользователя...")
    print("📱 Напишите боту @Clever_driver_bot: /start")
    print("⏳ Ожидание 30 секунд...")
    
    for i in range(30, 0, -1):
        print(f"⏰ Осталось: {i} сек", end="\r")
        time.sleep(1)
    
    print("\n🔍 Проверка обновлений...")

def check_updates():
    """Проверяет обновления бота"""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                updates = result.get('result', [])
                print(f"📋 Найдено обновлений: {len(updates)}")
                
                if updates:
                    print("✅ Обновления найдены!")
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
                            
                            # Попробуем отправить ответ
                            chat_id = chat.get('id')
                            if chat_id:
                                send_test_message(chat_id, user.get('username', ''))
                                return True
                else:
                    print("❌ Обновлений не найдено")
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

def send_test_message(chat_id, username):
    """Отправляет тестовое сообщение"""
    print(f"📤 Отправка тестового сообщения в {chat_id} (@{username})")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': f'🔧 Тест связи успешен!\n\n👤 Ваш username: @{username}\n🆔 Ваш ID: {chat_id}\n\n✅ Теперь можно привязать аккаунт!'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Тестовое сообщение отправлено!")
                print(f"📋 ID сообщения: {result['result']['message_id']}")
                return True
            else:
                print(f"❌ API ошибка: {result.get('description', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

def main():
    print("🚀 Установка связи с ботом")
    print("=" * 50)
    print("📋 Инструкции:")
    print("1. Откройте мобильное приложение Telegram")
    print("2. Найдите бота: @Clever_driver_bot")
    print("3. Напишите: /start")
    print("4. Дождитесь ответа от бота")
    print("=" * 50)
    
    input("⏸️ Нажмите Enter, когда будете готовы начать...")
    
    # Ждем сообщение
    wait_for_user_message()
    
    # Проверяем обновления
    if check_updates():
        print("\n✅ Связь установлена!")
        print("💡 Теперь попробуйте привязать аккаунт через веб-интерфейс")
    else:
        print("\n❌ Связь не установлена")
        print("💡 Возможные причины:")
        print("   - Вы писали с другого аккаунта")
        print("   - Бот заблокирован")
        print("   - Проблемы с сетью")
        print("   - Настройки приватности")

if __name__ == "__main__":
    main() 