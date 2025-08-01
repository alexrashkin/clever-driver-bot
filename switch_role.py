#!/usr/bin/env python3
"""
Скрипт для быстрого переключения Telegram ID между ролями админа и водителя
"""

import sqlite3
import sys

def switch_telegram_role():
    """Переключает Telegram ID между админом и водителем"""
    
    # Ваш Telegram ID
    YOUR_TELEGRAM_ID = 946872573
    
    # Временные ID для отвязки
    TEMP_ADMIN_ID = 888888888
    TEMP_DRIVER_ID = 777777777
    
    conn = sqlite3.connect('driver.db')
    cursor = conn.cursor()
    
    try:
        # Проверяем текущее состояние
        cursor.execute('SELECT login, telegram_id, role FROM users WHERE telegram_id = ?', (YOUR_TELEGRAM_ID,))
        current_user = cursor.fetchone()
        
        if current_user:
            current_role = current_user[2]
            print(f"Текущая роль: {current_role}")
            
            if current_role == 'admin':
                # Переключаем с админа на водителя
                print("Переключаем с админа на водителя...")
                
                # Отвязываем от админа
                cursor.execute('UPDATE users SET telegram_id = ? WHERE telegram_id = ?', (TEMP_ADMIN_ID, YOUR_TELEGRAM_ID))
                print(f"Отвязано от админа: {cursor.rowcount} записей")
                
                # Привязываем к водителю
                cursor.execute('UPDATE users SET telegram_id = ? WHERE login = "driver"', (YOUR_TELEGRAM_ID,))
                print(f"Привязано к водителю: {cursor.rowcount} записей")
                
                print("✅ Теперь вы водитель!")
                
            elif current_role == 'driver':
                # Переключаем с водителя на админа
                print("Переключаем с водителя на админа...")
                
                # Отвязываем от водителя
                cursor.execute('UPDATE users SET telegram_id = ? WHERE login = "driver"', (TEMP_DRIVER_ID,))
                print(f"Отвязано от водителя: {cursor.rowcount} записей")
                
                # Привязываем к админу (находим админа с временным ID)
                cursor.execute('UPDATE users SET telegram_id = ? WHERE role = "admin" AND telegram_id = ?', (YOUR_TELEGRAM_ID, TEMP_ADMIN_ID))
                print(f"Привязано к админу: {cursor.rowcount} записей")
                
                print("✅ Теперь вы админ!")
            else:
                print(f"Неизвестная роль: {current_role}")
        else:
            print("Ваш Telegram ID не привязан ни к одной роли")
            print("Привязываем к админу...")
            cursor.execute('UPDATE users SET telegram_id = ? WHERE role = "admin" AND telegram_id = ?', (YOUR_TELEGRAM_ID, TEMP_ADMIN_ID))
            print(f"Привязано к админу: {cursor.rowcount} записей")
        
        conn.commit()
        
        # Показываем текущее состояние
        print("\nТекущее состояние:")
        cursor.execute('SELECT login, telegram_id, role FROM users ORDER BY role, login')
        results = cursor.fetchall()
        for r in results:
            if r[1] == YOUR_TELEGRAM_ID:
                print(f"  {r[0] or 'None'} (Telegram: {r[1]} - ВЫ, Role: {r[2]})")
            else:
                print(f"  {r[0] or 'None'} (Telegram: {r[1]}, Role: {r[2]})")
                
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    switch_telegram_role() 