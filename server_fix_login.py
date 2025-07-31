#!/usr/bin/env python3
import sqlite3

def fix_login_issue():
    """Исправляем проблему с login на сервере"""
    print("🔧 Исправляем проблему с login на сервере...")
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Показываем текущее состояние
        print("📊 Текущее состояние базы данных:")
        cursor.execute("SELECT id, telegram_id, login, role FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Telegram: {user[1]}, Login: '{user[2]}', Role: {user[3]}")
        
        # Проверяем, есть ли записи с login = 'None'
        cursor.execute("SELECT COUNT(*) FROM users WHERE login = 'None'")
        count = cursor.fetchone()[0]
        print(f"\n📊 Записей с login = 'None': {count}")
        
        if count > 0:
            # Исправляем записи с login = 'None' на NULL
            cursor.execute("UPDATE users SET login = NULL WHERE login = 'None'")
            affected = cursor.rowcount
            print(f"✅ Исправлено записей: {affected}")
            
            # Проверяем результат
            print("\n📊 После исправления:")
            cursor.execute("SELECT id, telegram_id, login, role FROM users")
            users = cursor.fetchall()
            for user in users:
                print(f"  ID: {user[0]}, Telegram: {user[1]}, Login: '{user[2]}', Role: {user[3]}")
        else:
            print("✅ Проблемных записей не найдено")
        
        # Тестируем создание пользователя
        print("\n🧪 Тестируем создание пользователя 'testuser'...")
        cursor.execute("SELECT COUNT(*) FROM users WHERE login = 'testuser'")
        exists = cursor.fetchone()[0]
        if exists > 0:
            print("⚠️ Пользователь testuser уже существует, удаляем...")
            cursor.execute("DELETE FROM users WHERE login = 'testuser'")
        
        # Пытаемся создать тестового пользователя
        cursor.execute("""
            INSERT INTO users (login, password_hash, first_name, last_name, auth_type, role)
            VALUES (?, ?, ?, ?, 'login', ?)
        """, ("testuser", "test_hash", "Тест", "Пользователь", "driver"))
        
        user_id = cursor.lastrowid
        print(f"✅ Тестовый пользователь создан с ID: {user_id}")
        
        # Удаляем тестового пользователя
        cursor.execute("DELETE FROM users WHERE login = 'testuser'")
        print("🧹 Тестовый пользователь удален")
        
        conn.commit()
        conn.close()
        print("\n🎉 Проблема исправлена! Теперь можно создавать новых пользователей.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_login_issue() 