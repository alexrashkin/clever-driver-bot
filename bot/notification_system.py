#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from bot.database import db
from bot.utils import create_work_notification

logger = logging.getLogger(__name__)

class NotificationSystem:
    """Система отправки уведомлений с подтверждениями"""
    
    def __init__(self, bot_application=None):
        self.bot = bot_application
    
    async def send_notification_with_confirmation(self, notification_type, sender_info, 
                                                 recipients, notification_text=None, 
                                                 custom_confirmation=True):
        """
        Отправить уведомления с системой подтверждений
        
        Args:
            notification_type (str): Тип уведомления ('manual', 'automatic', 'arrival', 'departure')
            sender_info (dict): Информация об отправителе
            recipients (list): Список получателей (telegram_id)
            notification_text (str): Текст уведомления
            custom_confirmation (bool): Отправлять ли кастомные подтверждения
        
        Returns:
            dict: Результат отправки
        """
        # Создаем лог уведомления
        notification_log_id = db.create_notification_log(
            notification_type=notification_type,
            sender_id=sender_info.get('id'),
            sender_telegram_id=sender_info.get('telegram_id'),
            sender_login=sender_info.get('login'),
            notification_text=notification_text or create_work_notification()
        )
        
        if not notification_log_id:
            logger.error("Не удалось создать лог уведомления")
            return {'success': False, 'error': 'Ошибка создания лога'}
        
        # Добавляем получателей в детали
        for recipient_id in recipients:
            user_info = db.get_user_by_telegram_id(recipient_id)
            recipient_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() if user_info else None
            
            db.add_notification_detail(
                notification_log_id=notification_log_id,
                recipient_telegram_id=recipient_id,
                recipient_name=recipient_name,
                status="pending"
            )
        
        # Отправляем уведомления
        sent_count = 0
        failed_count = 0
        successful_recipients = []
        failed_recipients = []
        
        for recipient_id in recipients:
            try:
                if self.bot:
                    await self.bot.send_message(
                        chat_id=recipient_id,
                        text=notification_text or create_work_notification()
                    )
                    
                    # Обновляем статус на успешный
                    db.update_notification_detail(
                        notification_log_id=notification_log_id,
                        recipient_telegram_id=recipient_id,
                        status="sent"
                    )
                    
                    sent_count += 1
                    user_info = db.get_user_by_telegram_id(recipient_id)
                    if user_info:
                        successful_recipients.append(f"• {user_info.get('first_name', '')} {user_info.get('last_name', '')}")
                    else:
                        successful_recipients.append(f"• ID: {recipient_id}")
                    
                    logger.info(f"✅ Уведомление отправлено: {recipient_id}")
                    
                else:
                    logger.error("Bot application не инициализирован")
                    failed_count += 1
                    
            except Exception as e:
                error_msg = str(e)
                db.update_notification_detail(
                    notification_log_id=notification_log_id,
                    recipient_telegram_id=recipient_id,
                    status="failed",
                    error_message=error_msg
                )
                
                failed_count += 1
                user_info = db.get_user_by_telegram_id(recipient_id)
                if user_info:
                    failed_recipients.append(f"• {user_info.get('first_name', '')} {user_info.get('last_name', '')} (ошибка: {error_msg})")
                else:
                    failed_recipients.append(f"• ID: {recipient_id} (ошибка: {error_msg})")
                
                logger.error(f"❌ Ошибка отправки уведомления {recipient_id}: {e}")
        
        # Завершаем лог
        db.complete_notification_log(notification_log_id, sent_count, failed_count)
        
        # Отправляем подтверждения
        if custom_confirmation and sent_count > 0:
            await self._send_confirmation_messages(
                notification_log_id, sender_info, successful_recipients, 
                failed_recipients, notification_text, notification_type
            )
        
        return {
            'success': sent_count > 0,
            'notification_log_id': notification_log_id,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_recipients': len(recipients),
            'successful_recipients': successful_recipients,
            'failed_recipients': failed_recipients
        }
    
    async def _send_confirmation_messages(self, notification_log_id, sender_info, 
                                         successful_recipients, failed_recipients, 
                                         notification_text, notification_type):
        """Отправить подтверждения отправителям"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Формируем подтверждение для водителей
        if sender_info.get('role') == 'driver' or notification_type in ['manual', 'automatic']:
            await self._send_driver_confirmation(
                notification_log_id, sender_info, successful_recipients, 
                failed_recipients, notification_text, current_time
            )
        
        # Формируем подтверждение для администраторов
        await self._send_admin_confirmation(
            notification_log_id, sender_info, successful_recipients, 
            failed_recipients, notification_text, current_time, notification_type
        )
        
        # Отмечаем, что подтверждения отправлены
        db.mark_confirmation_sent(notification_log_id)
    
    async def _send_driver_confirmation(self, notification_log_id, sender_info, 
                                       successful_recipients, failed_recipients, 
                                       notification_text, current_time):
        """Отправить подтверждение водителям"""
        if not self.bot:
            return
        
        # Получаем всех водителей
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'driver' AND telegram_id IS NOT NULL")
        drivers = cursor.fetchall()
        conn.close()
        
        if not drivers:
            return
        
        # Формируем текст подтверждения
        confirmation_text = f"""✅ Уведомления отправлены {len(successful_recipients)} получателям:
📅 Время: {current_time}
📢 Текст: '{notification_text}'

🎯 Успешно отправлено:
{chr(10).join(successful_recipients)}"""
        
        if failed_recipients:
            confirmation_text += f"""

❌ Ошибки отправки:
{chr(10).join(failed_recipients)}"""
        
        # Отправляем подтверждение водителям
        for (driver_telegram_id,) in drivers:
            try:
                await self.bot.send_message(
                    chat_id=driver_telegram_id,
                    text=confirmation_text
                )
                logger.info(f"✅ Подтверждение отправлено водителю {driver_telegram_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки подтверждения водителю {driver_telegram_id}: {e}")
    
    async def _send_admin_confirmation(self, notification_log_id, sender_info, 
                                      successful_recipients, failed_recipients, 
                                      notification_text, current_time, notification_type):
        """Отправить подтверждение администраторам"""
        if not self.bot:
            return
        
        # Получаем всех администраторов
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'admin' AND telegram_id IS NOT NULL")
        admins = cursor.fetchall()
        conn.close()
        
        if not admins:
            return
        
        # Формируем текст подтверждения для админов
        sender_name = f"{sender_info.get('first_name', '')} {sender_info.get('last_name', '')}".strip()
        if not sender_name:
            sender_name = sender_info.get('login', 'Неизвестный пользователь')
        
        confirmation_text = f"""🔔 УВЕДОМЛЕНИЯ ОТПРАВЛЕНЫ
📅 Время: {current_time}
👤 Отправитель: {sender_name}
📝 Тип: {notification_type}
📢 Текст: '{notification_text}'

🎯 Получатели ({len(successful_recipients)}):
{chr(10).join(successful_recipients)}"""
        
        if failed_recipients:
            confirmation_text += f"""

❌ Ошибки ({len(failed_recipients)}):
{chr(10).join(failed_recipients)}"""
        
        # Отправляем подтверждение администраторам
        for (admin_telegram_id,) in admins:
            try:
                await self.bot.send_message(
                    chat_id=admin_telegram_id,
                    text=confirmation_text
                )
                logger.info(f"✅ Подтверждение отправлено администратору {admin_telegram_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки подтверждения администратору {admin_telegram_id}: {e}")
    
    def get_notification_statistics(self, days=7):
        """Получить статистику уведомлений за последние дни"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                notification_type,
                COUNT(*) as total_notifications,
                SUM(sent_count) as total_sent,
                SUM(failed_count) as total_failed,
                AVG(sent_count) as avg_sent,
                AVG(failed_count) as avg_failed
            FROM notification_logs 
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY notification_type
        '''.format(days))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            columns = ['notification_type', 'total_notifications', 'total_sent', 
                      'total_failed', 'avg_sent', 'avg_failed']
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_user_notification_history(self, user_id, limit=10):
        """Получить историю уведомлений пользователя"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, notification_type, notification_text, recipients_count,
                   sent_count, failed_count, created_at, completed_at
            FROM notification_logs 
            WHERE sender_id = ? OR sender_telegram_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            columns = ['id', 'notification_type', 'notification_text', 'recipients_count',
                      'sent_count', 'failed_count', 'created_at', 'completed_at']
            return [dict(zip(columns, row)) for row in rows]
        return []

# Глобальный экземпляр системы уведомлений
notification_system = NotificationSystem() 