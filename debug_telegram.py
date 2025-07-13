#!/usr/bin/env python3
"""
Детальная диагностика Telegram уведомлений
"""

import sys
import os
import requests
import json
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from bot.utils import create_work_notification

def debug_telegram_send():
    """Детальная диагностика отправки в Telegram"""
    print("🔍 Детальная диагностика Telegram...")
    
    token = config.TELEGRAM_TOKEN
    chat_id = config.NOTIFICATION_CHAT_ID
    
    print(f"📋 Токен: {token[:10]}...")
    print(f"💬 Chat ID: {chat_id}")
    
    # Тест 1: Проверка бота
    print("\n1️⃣ Проверка бота...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        print(f"   HTTP статус: {response.status_code}")
        print(f"   Ответ: {response.text}")
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"   ✅ Бот работает: {bot_info['result']['first_name']} (@{bot_info['result']['username']})")
            else:
                print(f"   ❌ Ошибка бота: {bot_info.get('description')}")
                return False
        else:
            print(f"   ❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False
    
    # Тест 2: Отправка тестового сообщения
    print("\n2️⃣ Отправка тестового сообщения...")
    test_message = f"🧪 Тестовое сообщение от {datetime.now().strftime('%H:%M:%S')}"
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": test_message
            },
            timeout=15
        )
        
        print(f"   HTTP статус: {response.status_code}")
        print(f"   Ответ: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("   ✅ Тестовое сообщение отправлено успешно!")
                return True
            else:
                print(f"   ❌ Ошибка отправки: {result.get('description')}")
                return False
        else:
            print(f"   ❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка отправки: {e}")
        return False

def debug_work_notification():
    """Детальная диагностика уведомления о работе"""
    print("\n3️⃣ Диагностика уведомления о работе...")
    
    try:
        notification_text = create_work_notification()
        print(f"   📝 Текст уведомления: {notification_text}")
        
        token = config.TELEGRAM_TOKEN
        chat_id = config.NOTIFICATION_CHAT_ID
        
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": notification_text
            },
            timeout=15
        )
        
        print(f"   HTTP статус: {response.status_code}")
        print(f"   Ответ: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("   ✅ Уведомление о работе отправлено успешно!")
                return True
            else:
                print(f"   ❌ Ошибка отправки: {result.get('description')}")
                return False
        else:
            print(f"   ❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка отправки: {e}")
        return False

def main():
    """Основная функция"""
    print("🤖 Детальная диагностика Telegram уведомлений")
    print("=" * 60)
    
    # Тест подключения
    if not debug_telegram_send():
        print("\n❌ Проблема с подключением к Telegram API")
        return
    
    # Тест уведомления о работе
    if not debug_work_notification():
        print("\n❌ Проблема с отправкой уведомления о работе")
        return
    
    print("\n✅ Все тесты прошли успешно!")
    print("💡 Если вы не получаете сообщения, проверьте:")
    print("   - Бот добавлен в нужный чат")
    print("   - У бота есть права на отправку сообщений")
    print("   - Chat ID указан правильно")

if __name__ == "__main__":
    main() 