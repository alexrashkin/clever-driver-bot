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
                print("SUCCESS: Bot is working!")
                print(f"Name: {bot_info.get('first_name')}")
                print(f"Username: @{bot_info.get('username')}")
                print(f"ID: {bot_info.get('id')}")
                return True
            else:
                print(f"ERROR: {data.get('description')}")
                return False
        else:
            print(f"HTTP ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        return False

def test_send_message():
    """Тестирует отправку сообщения (только для отладки)"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': '7824059826',  # ID бота (для теста)
            'text': 'Test message from bot'
        }
        
        response = requests.post(url, json=data, timeout=10)
        print(f"Test message status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Test message error: {e}")

if __name__ == "__main__":
    print("Checking bot status...")
    print("=" * 50)
    
    if check_bot_status():
        print("\nBot is working correctly!")
        print("Now try to send /start to the bot")
    else:
        print("\nBot has problems!")
        print("Check bot configuration")
    
    print("\n" + "=" * 50)
    print("Testing bot message sending...")
    test_send_message() 