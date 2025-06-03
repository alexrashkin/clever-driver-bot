#!/usr/bin/env python3
"""
Скрипт для настройки IP адреса ВМ в файлах Clever Driver Bot
"""

import os
import sys

def update_ip_in_file(filename, old_ip, new_ip):
    """Обновляет IP адрес в файле"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Замена всех вхождений старого IP на новый
        updated_content = content.replace(old_ip, new_ip)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Обновлен {filename}: {old_ip} → {new_ip}")
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления {filename}: {e}")
        return False

def get_server_ip():
    """Получает внешний IP сервера"""
    try:
        import requests
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text.strip()
    except:
        try:
            # Fallback - получение локального IP
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

def main():
    """Основная функция"""
    print("🚗 Clever Driver Bot - Настройка IP адреса ВМ")
    print("=" * 50)
    
    # Текущий IP (из Windows машины)
    OLD_IP = "192.168.0.104"
    
    # Получение нового IP
    if len(sys.argv) > 1:
        NEW_IP = sys.argv[1]
    else:
        detected_ip = get_server_ip()
        if detected_ip:
            print(f"🔍 Обнаружен IP: {detected_ip}")
            NEW_IP = input(f"Использовать {detected_ip}? (Enter/новый IP): ").strip()
            if not NEW_IP:
                NEW_IP = detected_ip
        else:
            NEW_IP = input("Введите IP адрес ВМ: ").strip()
    
    if not NEW_IP:
        print("❌ IP адрес не указан!")
        sys.exit(1)
    
    print(f"🔄 Обновление {OLD_IP} → {NEW_IP}")
    
    # Файлы для обновления
    files_to_update = [
        'https_simple_server.py',
        'telegram_bot_handler.py',
        'check_status.py',
        'README_GEO_BOT.md'
    ]
    
    updated_count = 0
    for filename in files_to_update:
        if os.path.exists(filename):
            if update_ip_in_file(filename, OLD_IP, NEW_IP):
                updated_count += 1
        else:
            print(f"⚠️ Файл не найден: {filename}")
    
    print(f"\n🎉 Обновлено файлов: {updated_count}/{len(files_to_update)}")
    print(f"🌐 Новый адрес сервера: https://{NEW_IP}:8443")
    print(f"🤖 Telegram бот будет работать с новым IP")
    
    # Создание .env файла
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(f"# Clever Driver Bot Environment\n")
        f.write(f"SERVER_IP={NEW_IP}\n")
        f.write(f"HTTPS_PORT=8443\n")
        f.write(f"BOT_TOKEN=7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc\n")
        f.write(f"CHAT_ID=946872573\n")
        f.write(f"HOME_LAT=55.676803\n")
        f.write(f"HOME_LON=37.523510\n")
    
    print(f"✅ Создан файл .env с конфигурацией")

if __name__ == "__main__":
    main() 