#!/usr/bin/env python3
"""
Скрипт для получения Chat ID из Telegram
"""

import sys
import os
import requests
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def get_updates():
    """Получение обновлений от бота для определения Chat ID"""
    print("🔍 Получение обновлений от бота...")
    
    token = config.TELEGRAM_TOKEN
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
        if response.status_code == 200:
            updates = response.json()
            if updates.get('ok'):
                results = updates.get('result', [])
                if results:
                    print(f"📋 Найдено {len(results)} обновлений:")
                    for update in results:
                        message = update.get('message', {})
                        chat = message.get('chat', {})
                        chat_id = chat.get('id')
                        chat_type = chat.get('type')
                        chat_title = chat.get('title', 'Личный чат')
                        
                        print(f"   💬 Chat ID: {chat_id}")
                        print(f"   📝 Тип: {chat_type}")
                        print(f"   🏷️ Название: {chat_title}")
                        print(f"   📅 Время: {datetime.fromtimestamp(message.get('date', 0))}")
                        print()
                else:
                    print("❌ Обновлений не найдено")
                    print("💡 Отправьте сообщение боту, чтобы получить Chat ID")
            else:
                print(f"❌ Ошибка API: {updates.get('description')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

def main():
    """Основная функция"""
    print("📱 Получение Chat ID")
    print("=" * 30)
    
    print(f"🤖 Токен бота: {config.TELEGRAM_TOKEN[:10]}...")
    print(f"💬 Текущий Chat ID: {config.NOTIFICATION_CHAT_ID}")
    print()
    
    get_updates()
    
    print("💡 Инструкция:")
    print("1. Отправьте сообщение боту")
    print("2. Запустите этот скрипт снова")
    print("3. Скопируйте нужный Chat ID в config/settings.py")

if __name__ == "__main__":
    main() 