#!/usr/bin/env python3
"""
Скрипт для удаления пользователей с неверными Telegram ID
"""
import sqlite3

def delete_bad_users():
    """Удаляет пользователей с неверными Telegram ID"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ПОЛЬЗОВАТЕЛИ С НЕВЕРНЫМИ TELEGRAM ID ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users WHERE telegram_id IN (999999999, 555555555, 444444444, 777777777)")
        bad_users = cursor.fetchall()
        
        for user in bad_users:
            user_id, login, telegram_id, role = user
            print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}")
        
        print(f"\nНайдено пользователей с неверными Telegram ID: {len(bad_users)}")
        
        if len(bad_users) == 0:
            print("✅ Нет пользователей с неверными Telegram ID")
            conn.close()
            return
        
        print("\n=== ПОДТВЕРЖДЕНИЕ ===")
        confirm = input("Удалить пользователей с неверными Telegram ID? (да/нет): ")
        
        if confirm.lower() not in ['да', 'yes', 'y', 'д']:
            print("❌ Операция отменена")
            conn.close()
            return
        
        print("\n=== УДАЛЕНИЕ ===")
        cursor.execute("DELETE FROM users WHERE telegram_id IN (999999999, 555555555, 444444444, 777777777)")
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Удалено пользователей: {deleted_count}")
        
        print("\n=== ОСТАВШИЕСЯ ПОЛЬЗОВАТЕЛИ ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users ORDER BY id")
        remaining_users = cursor.fetchall()
        
        for user in remaining_users:
            user_id, login, telegram_id, role = user
            print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}")
        
        print(f"\nОсталось пользователей: {len(remaining_users)}")
        
        conn.close()
        print("\n✅ Пользователи с неверными Telegram ID удалены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    delete_bad_users() 