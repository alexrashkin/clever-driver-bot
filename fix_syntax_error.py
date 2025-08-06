#!/usr/bin/env python3
"""
Скрипт для исправления синтаксической ошибки в handlers.py
"""

def fix_syntax_error():
    """Исправляет синтаксическую ошибку в handlers.py"""
    
    try:
        with open('bot/handlers.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Исправляем незакрытую строку
        old_text = '''        await update.message.reply_text(
            "Тестовый код привязки: **" + str(bind_code) + "**\n\n" +
            "Введите этот код на странице привязки аккаунта.\n" +
            "Код действителен 10 минут."'''
        
        new_text = '''        await update.message.reply_text(
            "Тестовый код привязки: **" + str(bind_code) + "**\\n\\n" +
            "Введите этот код на странице привязки аккаунта.\\n" +
            "Код действителен 10 минут.")'''
        
        content = content.replace(old_text, new_text)
        
        with open('bot/handlers.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Синтаксическая ошибка исправлена")
        
    except Exception as e:
        print(f"Ошибка при исправлении: {e}")

if __name__ == "__main__":
    fix_syntax_error()
