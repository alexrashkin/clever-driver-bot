#!/usr/bin/env python3
"""
Отладка восстановления пароля пользователя receiver
"""

import sys
import os

# Добавляем пути
current_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(current_dir, 'web')

sys.path.insert(0, current_dir)
sys.path.insert(0, web_dir)

def debug_receiver():
    """Отладка пользователя receiver"""
    print("🔍 Отладка пользователя receiver...")
    
    try:
        from bot.database import Database
        
        db = Database()
        
        # Проверяем пользователя receiver
        user = db.get_user_by_login("receiver")
        if user:
            print(f"✅ Пользователь receiver найден:")
            print(f"  ID: {user.get('id')}")
            print(f"  Login: {user.get('login')}")
            print(f"  Email: {user.get('email')}")
            print(f"  Role: {user.get('role')}")
            
            if user.get('email'):
                print("✅ Email есть в базе данных")
            else:
                print("❌ Email НЕТ в базе данных")
        else:
            print("❌ Пользователь receiver не найден")
            return
        
        # Тестируем восстановление пароля
        print("\n🧪 Тестирование восстановления пароля...")
        
        login = "receiver"
        success, result = db.create_password_reset_code(login)
        
        print(f"📧 Результат create_password_reset_code:")
        print(f"  Success: {success}")
        print(f"  Result: {result}")
        
        if success:
            print("✅ Код восстановления создан успешно")
            
            # Проверяем, создался ли код в базе
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, login, code, expires_at, used FROM password_reset_codes WHERE login = ? ORDER BY created_at DESC LIMIT 1", (login,))
            code_record = cursor.fetchone()
            conn.close()
            
            if code_record:
                code_id, code_login, code_value, expires_at, used = code_record
                print(f"✅ Код в базе данных:")
                print(f"  ID: {code_id}")
                print(f"  Login: {code_login}")
                print(f"  Code: {code_value}")
                print(f"  Expires: {expires_at}")
                print(f"  Used: {used}")
            else:
                print("❌ Код НЕ найден в базе данных")
        else:
            print(f"❌ Ошибка создания кода: {result}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def test_email_sending():
    """Тестируем отправку email"""
    print("\n📧 Тестирование отправки email...")
    
    try:
        from bot.email_utils import send_password_reset_email
        
        # Тестируем отправку email
        email = "r100aa@yandex.ru"
        login = "receiver"
        code = "TEST123"
        
        print(f"📧 Отправляем тестовый email:")
        print(f"  To: {email}")
        print(f"  Login: {login}")
        print(f"  Code: {code}")
        
        success = send_password_reset_email(email, login, code)
        
        if success:
            print("✅ Email отправлен успешно")
        else:
            print("❌ Ошибка отправки email")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании email: {e}")
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

def test_web_reset():
    """Тестируем веб-интерфейс восстановления"""
    print("\n🌐 Тестирование веб-интерфейса...")
    
    try:
        from web.app import app
        
        with app.test_client() as client:
            # Тестируем страницу восстановления пароля
            response = client.post('/forgot_password', data={'login': 'receiver'})
            print(f"📋 Статус ответа /forgot_password: {response.status_code}")
            
            if response.status_code == 302:  # Редирект
                print("✅ Страница восстановления отвечает (редирект)")
                
                # Проверяем, есть ли сообщение об ошибке
                response_text = response.get_data(as_text=True)
                if "Для восстановления пароля необходим email" in response_text:
                    print("❌ Найдена ошибка: 'Для восстановления пароля необходим email'")
                else:
                    print("✅ Ошибка не найдена в ответе")
            else:
                print(f"❌ Неожиданный статус: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании веб-интерфейса: {e}")

if __name__ == "__main__":
    print("🚀 Отладка восстановления пароля пользователя receiver")
    print("=" * 70)
    
    # Проверяем пользователя
    debug_receiver()
    
    # Проверяем конфигурацию email
    check_email_config()
    
    # Тестируем отправку email
    test_email_sending()
    
    # Тестируем веб-интерфейс
    test_web_reset()
    
    print("\n🎯 Отладка завершена!") 