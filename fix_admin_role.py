#!/usr/bin/env python3
import sqlite3

def fix_admin_role():
    """Исправляем роль администратора"""
    print("🔧 Исправляем роль администратора...")
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Проверяем текущую роль
        cursor.execute("SELECT telegram_id, first_name, role FROM users WHERE telegram_id = 946872573")
        user = cursor.fetchone()
        if user:
            print(f"👤 Текущая роль: {user[2]}")
            
            # Устанавливаем роль admin
            cursor.execute("UPDATE users SET role = 'admin' WHERE telegram_id = 946872573")
            conn.commit()
            
            # Проверяем результат
            cursor.execute("SELECT telegram_id, first_name, role FROM users WHERE telegram_id = 946872573")
            user = cursor.fetchone()
            print(f"✅ Новая роль: {user[2]}")
        else:
            print("❌ Пользователь не найден")
        
        conn.close()
        print("🎉 Роль исправлена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_admin_role() 