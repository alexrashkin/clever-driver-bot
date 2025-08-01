#!/usr/bin/env python3
"""
Скрипт для удаления всех пользователей из базы данных
"""
import sqlite3

def delete_all_users():
    """Удаляет всех пользователей из базы данных"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ТЕКУЩИЕ ПОЛЬЗОВАТЕЛИ ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users ORDER BY id")
        users = cursor.fetchall()
        
        for user in users:
            user_id, login, telegram_id, role = user
            print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}")
        
        print(f"\nВсего пользователей: {len(users)}")
        
        if len(users) == 0:
            print("✅ База данных уже пуста")
            conn.close()
            return
        
        print("\n=== ПОДТВЕРЖДЕНИЕ ===")
        confirm = input("Вы уверены, что хотите удалить ВСЕХ пользователей? (да/нет): ")
        
        if confirm.lower() not in ['да', 'yes', 'y', 'д']:
            print("❌ Операция отменена")
            conn.close()
            return
        
        print("\n=== УДАЛЕНИЕ ===")
        cursor.execute("DELETE FROM users")
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Удалено пользователей: {deleted_count}")
        
        print("\n=== ПРОВЕРКА ===")
        cursor.execute("SELECT COUNT(*) FROM users")
        remaining = cursor.fetchone()[0]
        print(f"Осталось пользователей: {remaining}")
        
        conn.close()
        print("\n✅ Все пользователи успешно удалены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    delete_all_users() 