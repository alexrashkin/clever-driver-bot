#!/usr/bin/env python3
"""
Скрипт для добавления таблицы приглашений в базу данных
"""

import sqlite3
import os
import sys

def update_database():
    """Добавляет таблицу приглашений в базу данных"""
    
    # Путь к базе данных
    db_path = "driver.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        print("🔍 Проверяем существующую структуру базы данных...")
        
        # Проверяем, существует ли таблица invitations
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invitations'")
        if c.fetchone():
            print("✅ Таблица invitations уже существует")
        else:
            print("📝 Создаем таблицу invitations...")
            
            # Создаем таблицу приглашений
            c.execute('''
                CREATE TABLE invitations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter_id INTEGER NOT NULL,
                    inviter_telegram_id BIGINT,
                    inviter_login TEXT,
                    invite_code TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    recipient_telegram_id BIGINT,
                    recipient_username TEXT,
                    recipient_first_name TEXT,
                    recipient_last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP,
                    FOREIGN KEY (inviter_id) REFERENCES users (id)
                )
            ''')
            
            print("✅ Таблица invitations создана успешно")
        
        # Проверяем существующие приглашения
        c.execute("SELECT COUNT(*) FROM invitations")
        count = c.fetchone()[0]
        print(f"📊 Всего приглашений в базе: {count}")
        
        if count > 0:
            print("\n📋 Существующие приглашения:")
            c.execute('''
                SELECT i.id, i.invite_code, i.status, i.created_at,
                       u1.first_name as inviter_first_name, u1.last_name as inviter_last_name,
                       u2.first_name as recipient_first_name, u2.last_name as recipient_last_name
                FROM invitations i
                LEFT JOIN users u1 ON i.inviter_id = u1.id
                LEFT JOIN users u2 ON i.recipient_telegram_id = u2.telegram_id
                ORDER BY i.created_at DESC
                LIMIT 10
            ''')
            
            rows = c.fetchall()
            for row in rows:
                inv_id, code, status, created, inv_fname, inv_lname, rec_fname, rec_lname = row
                inviter_name = f"{inv_fname or ''} {inv_lname or ''}".strip() or "Неизвестно"
                recipient_name = f"{rec_fname or ''} {rec_lname or ''}".strip() if rec_fname or rec_lname else "—"
                status_text = "⏳ Ожидает" if status == 'pending' else "✅ Принято"
                print(f"  {code}: {status_text} | Приглашающий: {inviter_name} | Получатель: {recipient_name}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Обновление базы данных завершено успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Обновление базы данных для системы приглашений")
    print("=" * 50)
    
    success = update_database()
    
    if success:
        print("\n🎉 Все готово! Система приглашений активирована.")
        print("Теперь водители и администраторы смогут:")
        print("  • Создавать приглашения с уникальными кодами")
        print("  • Отслеживать статус приглашений")
        print("  • Видеть, кто принял приглашение")
    else:
        print("\n💥 Обновление не удалось. Проверьте логи выше.")
        sys.exit(1) 