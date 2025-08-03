#!/usr/bin/env python3
"""
Проверка правильных настроек email для cleverdriver.ru
"""

def show_correct_settings():
    """Показываем правильные настройки для cleverdriver.ru"""
    print("📧 Правильные настройки email для cleverdriver.ru:")
    print("=" * 60)
    
    print("""
🔧 Настройки SMTP для cleverdriver.ru:

EMAIL_SMTP_SERVER=mail.cleverdriver.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=ваш-пароль-который-вы-установили
EMAIL_FROM_NAME=Умный водитель
EMAIL_FROM_ADDRESS=info@cleverdriver.ru

📋 Альтернативные варианты портов:
- Порт 587 (STARTTLS) - стандартный для современных серверов
- Порт 465 (SSL) - если 587 не работает
- Порт 25 (обычный SMTP) - устаревший, но может работать

🌐 Проверка доступности:
""")
    
    # Проверяем доступность разных портов
    import socket
    
    server = "mail.cleverdriver.ru"
    ports = [587, 465, 25]
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Порт {port} - ОТКРЫТ")
            else:
                print(f"❌ Порт {port} - ЗАКРЫТ")
        except Exception as e:
            print(f"❌ Порт {port} - ОШИБКА: {e}")

def check_current_settings():
    """Проверяем текущие настройки"""
    print("\n🔍 Текущие настройки в .env:")
    print("=" * 40)
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
            
        email_settings = [
            'EMAIL_SMTP_SERVER',
            'EMAIL_SMTP_PORT', 
            'EMAIL_USERNAME',
            'EMAIL_FROM_ADDRESS'
        ]
        
        for setting in email_settings:
            for line in content.split('\n'):
                if line.startswith(setting):
                    print(f"  {line}")
                    break
    except Exception as e:
        print(f"❌ Ошибка чтения .env: {e}")

def suggest_fixes():
    """Предлагаем исправления"""
    print("\n🔧 Предлагаемые исправления:")
    print("=" * 40)
    
    print("""
1. Проверьте, что в ISPmanager создан почтовый ящик info@cleverdriver.ru

2. Убедитесь, что SMTP сервер настроен правильно:
   - Сервер: mail.cleverdriver.ru
   - Порт: 587 (или 465, если 587 не работает)

3. Проверьте пароль от почтового ящика

4. Убедитесь, что SSL сертификат выпущен для домена

5. Проверьте DNS записи:
   - MX запись для cleverdriver.ru
   - A запись для mail.cleverdriver.ru
""")

if __name__ == "__main__":
    print("🚀 Проверка настроек email для cleverdriver.ru")
    print("=" * 70)
    
    show_correct_settings()
    check_current_settings()
    suggest_fixes()
    
    print("\n🎯 Проверка завершена!") 