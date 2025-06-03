#!/usr/bin/env python3
"""
Простой обработчик команд для Telegram бота
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return
        
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    welcome_message = f"""
🚗 Добро пожаловать в Clever Driver Bot!

👋 Привет, {user.first_name}!

📱 Ваш Chat ID: {chat_id}

🎯 Этот бот будет уведомлять вас о прибытии домой.

🔒 Веб-интерфейс для iPhone (только HTTPS для геолокации):

⚠️ **ВАЖНО**: Если при нажатии кнопки видите белый экран:
1. Нажмите **"⋯"** (три точки) в правом верхнем углу
2. Выберите **"Открыть в Safari"** или **"Открыть в браузере"**
3. В Safari примите предупреждение о сертификате
4. Разрешите геолокацию

🔗 **Или скопируйте адрес вручную:**
🔒 HTTPS: `https://192.168.0.104:8443`
    """
    
    # Создаем inline кнопку только для HTTPS
    keyboard = [
        [InlineKeyboardButton("🔒 HTTPS сервер (геолокация)", url="https://192.168.0.104:8443")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)  # type: ignore
    logger.info(f"Пользователь {user.first_name} (ID: {chat_id}) запустил бота")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    if not update.message:
        return
        
    help_text = """
🚗 Clever Driver Bot - Помощь

📋 Доступные команды:
/start - Запуск бота и получение Chat ID
/help - Эта справка
/status - Статус системы отслеживания

🔒 Веб-интерфейс доступен только по HTTPS (для геолокации)

❓ Как использовать:
1. Нажмите /start для получения кнопки
2. Нажмите кнопку HTTPS сервера
3. **При белом экране**: нажмите "⋯" → "Открыть в Safari"
4. Примите предупреждение о сертификате
5. Разрешите доступ к геолокации
6. Нажмите кнопки для тестирования

📱 **Для iPhone обязательно используйте Safari**, не встроенный браузер Telegram!

🔧 При проблемах проверьте:
• Включена ли геолокация в настройках
• Разрешен ли доступ для Safari/браузера

🔗 Прямая ссылка:
🔒 HTTPS: https://192.168.0.104:8443
    """
    
    # Добавляем кнопку только для HTTPS
    keyboard = [
        [InlineKeyboardButton("🔒 HTTPS сервер (геолокация)", url="https://192.168.0.104:8443")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup)  # type: ignore

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    if not update.effective_chat or not update.message:
        return
        
    status_text = """
📊 Статус Clever Driver Bot

🤖 Бот: ✅ Активен
🔒 HTTPS-сервер: ✅ Работает
📍 Отслеживание: 🏠 Дом (55.676803, 37.523510)
📱 Ваш Chat ID: {}

🎯 Готов к отправке уведомлений!

💡 Нажмите кнопку ниже для доступа к веб-интерфейсу:

⚠️ **При белом экране**: нажмите "⋯" → "Открыть в Safari"

🔗 Прямая ссылка:
🔒 HTTPS: https://192.168.0.104:8443
    """.format(update.effective_chat.id)
    
    # Кнопка только для HTTPS
    keyboard = [
        [InlineKeyboardButton("🔒 HTTPS сервер (геолокация)", url="https://192.168.0.104:8443")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(status_text, reply_markup=reply_markup)  # type: ignore

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик любых текстовых сообщений"""
    if not update.effective_chat or not update.effective_user or not update.message:
        return
        
    chat_id = update.effective_chat.id
    user = update.effective_user
    message_text = update.message.text or ""
    
    logger.info(f"Сообщение от {user.first_name} (ID: {chat_id}): {message_text}")
    
    response = f"""
📱 Получено сообщение: "{message_text}"

💬 Ваш Chat ID: {chat_id}

🔧 Используйте команды:
/start - Начало работы
/help - Помощь
/status - Статус системы

🔒 Или нажмите кнопку для быстрого доступа к HTTPS серверу:

⚠️ **При белом экране**: нажмите "⋯" → "Открыть в Safari"
    """
    
    # Кнопка быстрого доступа только для HTTPS
    keyboard = [
        [InlineKeyboardButton("🔒 HTTPS сервер (геолокация)", url="https://192.168.0.104:8443")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup)  # type: ignore

def main():
    """Запуск бота"""
    logger.info("🤖 Запуск Telegram бота...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Обработчик всех текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Бот готов к работе!")
    logger.info("📱 Напишите боту @Clever_driver_bot команду /start")
    
    # Запуск бота
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main() 