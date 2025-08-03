#!/usr/bin/env python3
"""
Отладка веб-приложения
"""

import sys
import os

# Добавляем пути как в run_web.py
current_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(current_dir, 'web')

sys.path.insert(0, current_dir)
sys.path.insert(0, web_dir)

def debug_web_app():
    """Отладка веб-приложения"""
    print("🔍 Отладка веб-приложения...")
    
    try:
        from bot.database import Database
        from web.app import app
        
        # Создаем экземпляр БД
        db = Database()
        print(f"🗄️ Путь к БД: {db.db_path}")
        
        # Проверяем пользователей через БД напрямую
        users = db.get_all_users()
        print(f"👥 Пользователи через БД ({len(users)}):")
        
        receiver_db = None
        for user in users:
            user_id = user.get('id')
            login = user.get('login')
            email = user.get('email')
            role = user.get('role')
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
            
            if login == 'receiver':
                receiver_db = user
        
        if receiver_db:
            print(f"\n🎯 Пользователь receiver в БД:")
            print(f"  Email: {receiver_db.get('email')}")
        
        # Тестируем маршрут админ-панели
        print("\n🌐 Тестирование маршрута /admin/users...")
        
        with app.test_client() as client:
            # Симулируем сессию админа
            with client.session_transaction() as sess:
                sess['telegram_id'] = 946872573  # ID админа
            
            # Делаем запрос к админ-панели
            response = client.get('/admin/users')
            print(f"📋 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Админ-панель отвечает")
                
                # Проверяем, есть ли email в ответе
                response_text = response.get_data(as_text=True)
                
                if 'r100aa@yandex.ru' in response_text:
                    print("✅ Email найден в ответе веб-приложения")
                else:
                    print("❌ Email НЕ найден в ответе веб-приложения")
                    print("🔍 Ищем email в ответе...")
                    
                    # Ищем email в HTML
                    if 'receiver' in response_text:
                        print("✅ Пользователь receiver найден в ответе")
                        # Ищем строку с receiver
                        lines = response_text.split('\n')
                        for i, line in enumerate(lines):
                            if 'receiver' in line:
                                print(f"📄 Строка {i}: {line.strip()}")
                                # Проверяем следующие строки
                                for j in range(i, min(i+5, len(lines))):
                                    if 'email' in lines[j].lower() or 'yandex' in lines[j].lower():
                                        print(f"📄 Строка {j}: {lines[j].strip()}")
                    else:
                        print("❌ Пользователь receiver НЕ найден в ответе")
            else:
                print(f"❌ Ошибка доступа к админ-панели: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def check_template():
    """Проверяем шаблон админ-панели"""
    print("\n📄 Проверка шаблона admin_users.html...")
    
    template_path = "web/templates/admin_users.html"
    if os.path.exists(template_path):
        print(f"✅ Шаблон найден: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем, есть ли код для отображения email
        if 'user.email' in content:
            print("✅ Код для отображения email найден в шаблоне")
        else:
            print("❌ Код для отображения email НЕ найден в шаблоне")
            
        # Проверяем, есть ли колонка Email
        if 'Email' in content:
            print("✅ Колонка Email найдена в шаблоне")
        else:
            print("❌ Колонка Email НЕ найдена в шаблоне")
    else:
        print(f"❌ Шаблон не найден: {template_path}")

if __name__ == "__main__":
    print("🚀 Отладка веб-приложения")
    print("=" * 60)
    
    debug_web_app()
    check_template()
    
    print("\n🎯 Отладка завершена!") 