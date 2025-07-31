#!/usr/bin/env python3
import requests
import json

# Токен бота из конфигурации
BOT_TOKEN = "7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc"

def check_bot_status():
    """Проверяет статус бота через Telegram API"""
    try:
        # Получаем информацию о боте
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print("✅ Бот работает!")
                print(f"Имя: {bot_info.get('first_name')}")
                print(f"Username: @{bot_info.get('username')}")
                print(f"ID: {bot_info.get('id')}")
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_send_message():
    """Тестирует отправку сообщения (только для отладки)"""
    try:
        # Этот метод требует chat_id, поэтому просто проверяем доступность API
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                print(f"📨 Последние обновления: {len(updates)}")
                if updates:
                    print("Последние сообщения:")
                    for update in updates[-3:]:  # Показываем последние 3
                        message = update.get('message', {})
                        if message:
                            user = message.get('from', {})
                            text = message.get('text', '')
                            print(f"  - {user.get('first_name', 'Unknown')}: {text}")
                return True
            else:
                print(f"❌ Ошибка получения обновлений: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка при получении обновлений: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении обновлений: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка статуса бота...")
    print("=" * 40)
    
    # Проверяем статус бота
    bot_ok = check_bot_status()
    
    if bot_ok:
        print("\n📨 Проверка получения сообщений...")
        test_send_message()
        
        print("\n💡 Если бот не отвечает на /start:")
        print("1. Проверьте, что сервис запущен: systemctl status driver-bot")
        print("2. Проверьте логи: tail -f logs/driver-bot.log")
        print("3. Перезапустите бота: systemctl restart driver-bot")
    else:
        print("\n❌ Бот недоступен. Проверьте:")
        print("1. Правильность токена")
        print("2. Подключение к интернету")
        print("3. Статус сервиса на сервере") 