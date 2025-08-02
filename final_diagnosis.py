#!/usr/bin/env python3
"""
Финальная диагностика проблемы
"""

import requests
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config

def check_bot_token():
    """Проверяет токен бота"""
    print("🔑 Проверка токена бота")
    print("=" * 40)
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot = result['result']
                print(f"✅ Токен работает")
                print(f"📋 Бот: @{bot.get('username', 'Нет')}")
                print(f"📋 ID: {bot.get('id', 'Нет')}")
                print(f"📋 Имя: {bot.get('first_name', 'Нет')}")
                return True
            else:
                print(f"❌ Токен недействителен: {result.get('description', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_webhook_status():
    """Проверяет статус webhook"""
    print(f"\n🔗 Проверка webhook")
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
                    print("⚠️ Webhook установлен - это может мешать getUpdates")
                    return True
                else:
                    print("✅ Webhook не установлен")
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

def clear_all_updates():
    """Очищает все обновления"""
    print(f"\n🗑️ Очистка всех обновлений")
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

def test_direct_send():
    """Тестирует прямую отправку"""
    print(f"\n📤 Тест прямой отправки")
    print("=" * 40)
    
    # Пробуем отправить сообщение напрямую
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': '@alexrashkin',
        'text': '🔧 Финальный тест связи'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"📡 HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Сообщение отправлено!")
                return True
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                print(f"❌ API ошибка: {error_msg}")
                return False
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('description', '')
                print(f"❌ Ошибка: {error_msg}")
            except:
                print("❌ HTTP 400 - Bad Request")
            return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🚀 Финальная диагностика проблемы")
    print("=" * 60)
    
    # Проверяем токен
    if not check_bot_token():
        print("❌ Проблема с токеном бота")
        return
    
    # Проверяем webhook
    has_webhook = check_webhook_status()
    
    # Очищаем обновления
    clear_all_updates()
    
    # Тестируем отправку
    if test_direct_send():
        print("\n✅ Проблема решена!")
        print("💡 Теперь попробуйте привязать аккаунт")
    else:
        print("\n❌ Проблема не решена")
        print("💡 Возможные причины:")
        print("1. Пользователь не писал боту /start")
        print("2. Настройки приватности блокируют сообщения")
        print("3. Пользователь заблокировал бота")
        print("4. Проблемы с Telegram API")
        
        print("\n🎯 Рекомендации:")
        print("1. Проверьте, что вы писали боту /start")
        print("2. Проверьте настройки приватности")
        print("3. Убедитесь, что бот не заблокирован")
        print("4. Попробуйте создать новый username")

if __name__ == "__main__":
    main() 