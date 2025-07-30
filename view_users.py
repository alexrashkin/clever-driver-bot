#!/usr/bin/env python3
"""
Скрипт для просмотра всех пользователей в базе данных Driver Bot
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from bot.database import Database

def main():
    """Основная функция для просмотра пользователей"""
    print("🚗 Driver Bot - Просмотр пользователей")
    print("=" * 50)
    
    try:
        db = Database()
        users = db.get_all_users()
        
        if not users:
            print("👥 Пользователи не найдены")
            return
        
        print(f"📊 Всего пользователей: {len(users)}")
        print()
        
        # Статистика по ролям
        roles_count = {}
        auth_count = {}
        
        for user in users:
            role = user.get('role', 'Без роли')
            auth_type = user.get('auth_type', 'Unknown')
            
            roles_count[role] = roles_count.get(role, 0) + 1
            auth_count[auth_type] = auth_count.get(auth_type, 0) + 1
        
        print("📈 Статистика по ролям:")
        for role, count in roles_count.items():
            role_emoji = {
                'admin': '👑',
                'driver': '🚗', 
                'recipient': '📱'
            }.get(role, '❓')
            print(f"  {role_emoji} {role}: {count}")
        
        print("\n🔐 Статистика по авторизации:")
        for auth, count in auth_count.items():
            auth_emoji = {
                'telegram': '📱',
                'login': '🔐'
            }.get(auth, '❓')
            print(f"  {auth_emoji} {auth}: {count}")
        
        print("\n" + "=" * 80)
        print(f"{'ID':<5} {'Имя/Логин':<20} {'Роль':<12} {'Авториз.':<10} {'Telegram ID':<15} {'Создан':<12}")
        print("=" * 80)
        
        for user in users:
            user_id = str(user.get('id', ''))
            
            # Имя пользователя
            if user.get('first_name') or user.get('last_name'):
                name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            elif user.get('login'):
                name = f"@{user.get('login')}"
            else:
                name = "Telegram пользователь"
            
            # Роль с эмодзи
            role = user.get('role', 'Без роли')
            role_display = {
                'admin': '👑 Админ',
                'driver': '🚗 Водитель', 
                'recipient': '📱 Получатель'
            }.get(role, '❓ ' + role)
            
            # Тип авторизации
            auth_type = user.get('auth_type', 'Unknown')
            auth_display = {
                'telegram': '📱 TG',
                'login': '🔐 Login'
            }.get(auth_type, '❓ ' + auth_type)
            
            # Telegram ID
            tg_id = str(user.get('telegram_id', '—'))
            
            # Дата создания
            created = user.get('created_at', '—')
            if created and len(created) >= 10:
                created = created[:10]
            
            print(f"{user_id:<5} {name:<20} {role_display:<12} {auth_display:<10} {tg_id:<15} {created:<12}")
        
        print("=" * 80)
        print(f"\n💡 Для удаления пользователя используйте веб-интерфейс: /admin/users")
        print(f"🌐 Или создайте админа: python3 -c \"from bot.database import Database; db=Database(); db.create_user_with_login('admin', 'password123', 'Admin', 'User', 'admin')\"")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 