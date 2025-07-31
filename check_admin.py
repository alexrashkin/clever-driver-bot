#!/usr/bin/env python3
"""
Скрипт для проверки админки и создания тестового администратора
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from bot.database import Database

def main():
    """Проверка и настройка админки"""
    print("🔧 Проверка админки Умный водитель")
    print("=" * 40)
    
    try:
        db = Database()
        
        # Проверяем есть ли администраторы
        users = db.get_all_users()
        admins = [u for u in users if u.get('role') == 'admin']
        
        print(f"📊 Всего пользователей: {len(users)}")
        print(f"👑 Администраторов: {len(admins)}")
        
        if admins:
            print("\n👑 Существующие администраторы:")
            for admin in admins:
                name = admin.get('first_name') or admin.get('login') or f"ID {admin.get('id')}"
                auth_type = "🔐 Логин" if admin.get('auth_type') == 'login' else "📱 Telegram"
                print(f"  • {name} ({auth_type})")
        else:
            print("\n⚠️  Администраторы не найдены!")
            
            # Предлагаем создать администратора
            create = input("\n❓ Создать тестового администратора? (y/n): ").lower().strip()
            if create in ['y', 'yes', 'да', 'д']:
                login = input("Введите логин (по умолчанию 'admin'): ").strip() or 'admin'
                password = input("Введите пароль (по умолчанию 'admin123'): ").strip() or 'admin123'
                
                success, result = db.create_user_with_login(login, password, 'Администратор', 'Системы', 'admin')
                
                if success:
                    print(f"✅ Администратор создан! Логин: {login}, Пароль: {password}")
                    print(f"🌐 Теперь можете войти на https://cleverdriver.ru/login")
                else:
                    print(f"❌ Ошибка создания: {result}")
        
        print("\n" + "=" * 60)
        print("🌐 ДОСТУПНЫЕ АДРЕСА АДМИНКИ:")
        print("  https://cleverdriver.ru/admin")
        print("  https://cleverdriver.ru/admin/users")
        print("\n🔐 ТРЕБОВАНИЯ:")
        print("  1. Войдите как администратор")
        print("  2. Роль должна быть 'admin'")
        print("\n🔧 ФУНКЦИИ АДМИНКИ:")
        print("  📊 Статистика пользователей")
        print("  📋 Таблица всех пользователей")
        print("  🗑️ Удаление пользователей")
        print("  🔍 Поиск дубликатов")
        
        print("\n💡 КОМАНДЫ ДЛЯ СЕРВЕРА:")
        print("  cd ~/clever-driver-bot")
        print("  ./restart_web_app.sh")
        print("  # или ручной перезапуск:")
        print("  source venv/bin/activate")
        print("  cd web && python app.py &")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 