#!/usr/bin/env python3
"""
Проверка статуса всех компонентов системы
"""

import requests
import subprocess

def check_web_server(url, name):
    """Проверка веб-сервера"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: {url} - работает")
            return True
        else:
            print(f"❌ {name}: {url} - ошибка {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: {url} - недоступен ({e})")
        return False

def check_ports():
    """Проверка открытых портов"""
    try:
        result = subprocess.run(
            ["netstat", "-an"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        ports = {
            "8080": "HTTP сервер",
            "8443": "HTTPS сервер"
        }
        
        for port, name in ports.items():
            if f":{port}" in result.stdout and "LISTENING" in result.stdout:
                print(f"✅ {name} (порт {port}): прослушивается")
            else:
                print(f"❌ {name} (порт {port}): не активен")
                
    except Exception as e:
        print(f"❌ Ошибка проверки портов: {e}")

def check_python_processes():
    """Проверка Python процессов"""
    try:
        result = subprocess.run(
            ["tasklist"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        python_count = result.stdout.count("python.exe")
        print(f"🐍 Python процессов запущено: {python_count}")
        
        if python_count >= 2:
            print("✅ Достаточно процессов для веб-сервера и бота")
        else:
            print("⚠️ Возможно, не все компоненты запущены")
            
    except Exception as e:
        print(f"❌ Ошибка проверки процессов: {e}")

def main():
    """Главная функция проверки"""
    print("🔍 Проверка статуса Clever Driver Bot системы...")
    print("=" * 60)
    
    # Проверка веб-серверов
    print("\n🌐 Веб-серверы:")
    http_ok = check_web_server("http://192.168.0.104:8080", "HTTP сервер")
    https_ok = check_web_server("https://192.168.0.104:8443", "HTTPS сервер")
    
    # Проверка портов
    print("\n🔌 Порты:")
    check_ports()
    
    # Проверка процессов
    print("\n⚙️ Процессы:")
    check_python_processes()
    
    # Итоговый статус
    print("\n" + "=" * 60)
    if http_ok or https_ok:
        print("✅ Система готова к работе!")
        print("📱 Теперь попробуйте команду /start в Telegram боте")
        print("🌐 HTTP: http://192.168.0.104:8080")
        print("🔒 HTTPS: https://192.168.0.104:8443")
    else:
        print("❌ Нужно запустить веб-сервер:")
        print("   python simple_web_server.py")
        print("   или")
        print("   python https_simple_server.py")
    
    print("\n🤖 Для Telegram бота также должен быть запущен:")
    print("   python telegram_bot_handler.py")

if __name__ == "__main__":
    main() 