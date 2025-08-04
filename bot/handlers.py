import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import db

logger = logging.getLogger(__name__)



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🚗 Привет, {user.first_name}!

Я бот сервиса «Умный водитель» — автоматическое отслеживание местоположения водителя и уведомления о прибытии/выезде из заданной зоны.

"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Доступные команды:
/start — Главное меню
/help — Эта справка
/bind — Привязать аккаунт к веб-приложению

"""
    await update.message.reply_text(help_text)





async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text("Используйте команды /start, /help, /bind.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте позже или обратитесь к администратору.")

async def bind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для привязки Telegram аккаунта к веб-приложению"""
    import random
    import sqlite3






    
    user = update.effective_user
    telegram_id = user.id
    username = user.username
    first_name = user.first_name
    chat_id = update.effective_chat.id
    
    # Генерируем код подтверждения
    bind_code = str(random.randint(100000, 999999))
    
    try:
        # Сохраняем код в базу данных
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Удаляем старые коды для этого пользователя
        cursor.execute("DELETE FROM telegram_bind_codes WHERE telegram_id = ?", (telegram_id,))
        
        # Добавляем новый код с локальным временем
        from datetime import datetime
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO telegram_bind_codes (telegram_id, username, first_name, chat_id, bind_code, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, username, first_name, chat_id, bind_code, local_time))
        
        conn.commit()
        conn.close()
        
        # Отправляем код пользователю
        message = f"🔐 Код для привязки аккаунта: {bind_code}\n\n"
        message += f"Используйте этот код в веб-приложении для завершения привязки.\n"
        message += f"Код действителен 10 минут."
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка при создании кода привязки: {e}")
        await update.message.reply_text("Произошла ошибка при создании кода. Попробуйте позже.") 