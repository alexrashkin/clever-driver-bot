#!/usr/bin/env python3
import sqlite3

def fix_none_string():
    """Заменяем строку 'None' на NULL в базе данных"""
    print("🔧 Заменяем строку 'None' на NULL...")
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Показываем текущее состояние
        print("📊 Текущее состояние:")
        cursor.execute("SELECT id, telegram_id, login, role FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Telegram: {user[1]}, Login: '{user[2]}', Role: {user[3]}")
        
        # Проверяем, есть ли записи с login = 'None'
        cursor.execute("SELECT COUNT(*) FROM users WHERE login = 'None'")
        count = cursor.fetchone()[0]
        print(f"\n📊 Записей с login = 'None': {count}")
        
        if count > 0:
            # Заменяем 'None' на NULL
            cursor.execute("UPDATE users SET login = NULL WHERE login = 'None'")
            affected = cursor.rowcount
            print(f"✅ Заменено записей: {affected}")
            
            # Проверяем результат
            print("\n📊 После замены:")
            cursor.execute("SELECT id, telegram_id, login, role FROM users")
            users = cursor.fetchall()
            for user in users:
                print(f"  ID: {user[0]}, Telegram: {user[1]}, Login: '{user[2]}', Role: {user[3]}")
        else:
            print("✅ Записей с login = 'None' не найдено")
        
        conn.commit()
        conn.close()
        print("\n🎉 Замена завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_none_string() 