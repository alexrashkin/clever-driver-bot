#!/usr/bin/env python3
"""
Детальная отладка отправки email
"""

import sys
import os

# Добавляем пути
current_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(current_dir, 'web')

sys.path.insert(0, current_dir)
sys.path.insert(0, web_dir)

def debug_email_sending():
    """Детальная отладка отправки email"""
    print("🔍 Детальная отладка отправки email...")
    
    try:
        from bot.database import Database
        from bot.email_utils import send_password_reset_email
        
        db = Database()
        
        # Проверяем пользователя receiver
        user = db.get_user_by_login("receiver")
        if user:
            print(f"✅ Пользователь receiver:")
            print(f"  Email: {user.get('email')}")
            
            if user.get('email'):
                print("✅ Email есть в базе данных")
                
                # Тестируем отправку email напрямую
                email = user.get('email')
                login = user.get('login')
                code = "TEST123"
                
                print(f"\n📧 Тестируем отправку email:")
                print(f"  To: {email}")
                print(f"  Login: {login}")
                print(f"  Code: {code}")
                print(f"  SMTP Server: 31.31.196.207")
                print(f"  SMTP Port: 587")
                
                # Тестируем отправку
                success = send_password_reset_email(email, login, code)
                
                if success:
                    print("✅ Email отправлен успешно!")
                else:
                    print("❌ Ошибка отправки email")
            else:
                print("❌ Email НЕТ в базе данных")
        else:
            print("❌ Пользователь receiver не найден")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def debug_create_password_reset_code():
    """Отладка метода create_password_reset_code"""
    print("\n🧪 Отладка метода create_password_reset_code...")
    
    try:
        from bot.database import Database
        
        db = Database()
        
        # Проверяем метод пошагово
        login = "receiver"
        
        # 1. Получаем пользователя
        user = db.get_user_by_login(login)
        print(f"1. Пользователь получен: {user is not None}")
        
        if user:
            print(f"   Email: {user.get('email')}")
            
            # 2. Проверяем email
            email = user.get('email')
            if email:
                print("2. Email найден")
                
                # 3. Тестируем отправку email
                print("3. Тестируем отправку email...")
                from bot.email_utils import send_password_reset_email
                
                success = send_password_reset_email(email, login, "TEST123")
                print(f"   Результат отправки: {success}")
                
                if success:
                    print("✅ Email отправляется успешно")
                else:
                    print("❌ Email НЕ отправляется")
            else:
                print("2. Email НЕ найден")
        else:
            print("1. Пользователь НЕ найден")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def check_email_config():
    """Проверяем конфигурацию email"""
    print("\n⚙️ Проверка конфигурации email...")
    
    try:
        from config.settings import config
        
        print(f"📧 Email настройки:")
        print(f"  EMAIL_ENABLED: {config.EMAIL_ENABLED}")
        print(f"  EMAIL_SMTP_SERVER: {config.EMAIL_SMTP_SERVER}")
        print(f"  EMAIL_SMTP_PORT: {config.EMAIL_SMTP_PORT}")
        print(f"  EMAIL_USERNAME: {config.EMAIL_USERNAME}")
        print(f"  EMAIL_FROM_ADDRESS: {config.EMAIL_FROM_ADDRESS}")
        
        if config.EMAIL_PASSWORD:
            print(f"  EMAIL_PASSWORD: {'*' * len(config.EMAIL_PASSWORD)} (установлен)")
        else:
            print(f"  EMAIL_PASSWORD: НЕ установлен")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке конфигурации: {e}")

def test_smtp_connection():
    """Тестируем SMTP подключение"""
    print("\n🔌 Тестирование SMTP подключения...")
    
    try:
        import socket
        
        server = "31.31.196.207"
        port = 587
        
        print(f"🔌 Подключение к {server}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((server, port))
        sock.close()
        
        if result == 0:
            print("✅ SMTP порт 587 доступен")
        else:
            print(f"❌ SMTP порт 587 недоступен (код ошибки: {result})")
            
            # Пробуем другие порты
            for test_port in [465, 25]:
                print(f"🔌 Пробуем порт {test_port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((server, test_port))
                sock.close()
                
                if result == 0:
                    print(f"✅ Порт {test_port} доступен")
                    break
                else:
                    print(f"❌ Порт {test_port} недоступен")
                    
    except Exception as e:
        print(f"❌ Ошибка при тестировании SMTP: {e}")

if __name__ == "__main__":
    print("🚀 Детальная отладка отправки email")
    print("=" * 70)
    
    # Проверяем конфигурацию
    check_email_config()
    
    # Тестируем SMTP подключение
    test_smtp_connection()
    
    # Отлаживаем отправку email
    debug_email_sending()
    
    # Отлаживаем метод восстановления
    debug_create_password_reset_code()
    
    print("\n🎯 Отладка завершена!") 