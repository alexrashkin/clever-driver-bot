#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для веб-отслеживания местоположений через браузер
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, session
from bot.database import db

logger = logging.getLogger(__name__)

# Создаем Blueprint для веб-отслеживания
location_web_tracker = Blueprint('location_web_tracker', __name__)

# Хранилище активных сессий отслеживания
active_tracking_sessions = {}

class WebLocationTracker:
    """Класс для управления веб-отслеживанием местоположений"""
    
    def __init__(self):
        self.active_sessions = {}
    
    def create_tracking_session(self, telegram_id, duration_minutes=60):
        """Создать сессию отслеживания"""
        try:
            # Проверяем, что пользователь является получателем
            user_info = db.get_user_by_telegram_id(telegram_id)
            if not user_info or user_info.get('role') != 'recipient':
                logger.warning(f"Попытка создать сессию для не-получателя: {telegram_id}")
                return None
            
            # Генерируем уникальный токен сессии
            session_token = str(uuid.uuid4())
            
            # Создаем сессию отслеживания
            session_data = {
                'telegram_id': telegram_id,
                'user_info': user_info,
                'duration_minutes': duration_minutes,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(minutes=duration_minutes),
                'is_active': True,
                'locations': []
            }
            
            self.active_sessions[session_token] = session_data
            
            logger.info(f"Создана веб-сессия отслеживания для {telegram_id}: {session_token}")
            return session_token
            
        except Exception as e:
            logger.error(f"Ошибка создания веб-сессии для {telegram_id}: {e}")
            return None
    
    def create_auto_session_for_user(self, telegram_id, duration_minutes=60):
        """Автоматически создать сессию для пользователя при входе в трекер"""
        try:
            # Проверяем, что пользователь является получателем
            user_info = db.get_user_by_telegram_id(telegram_id)
            if not user_info or user_info.get('role') != 'recipient':
                logger.warning(f"Попытка создать автосессию для не-получателя: {telegram_id}")
                return None
            
            # Проверяем, нет ли уже активной сессии для этого пользователя
            for token, session_data in self.active_sessions.items():
                if (session_data['telegram_id'] == telegram_id and 
                    session_data['is_active'] and 
                    datetime.now() < session_data['expires_at']):
                    logger.info(f"Найдена активная сессия для {telegram_id}: {token}")
                    return token
            
            # Создаем новую сессию
            return self.create_tracking_session(telegram_id, duration_minutes)
            
        except Exception as e:
            logger.error(f"Ошибка создания автосессии для {telegram_id}: {e}")
            return None
    
    def get_session_info(self, session_token):
        """Получить информацию о сессии"""
        return self.active_sessions.get(session_token)
    
    def add_location_to_session(self, session_token, latitude, longitude, accuracy=None, 
                               altitude=None, speed=None, heading=None):
        """Добавить местоположение в сессию"""
        try:
            session_data = self.active_sessions.get(session_token)
            if not session_data or not session_data['is_active']:
                return False
            
            # Проверяем, не истекла ли сессия
            if datetime.now() > session_data['expires_at']:
                session_data['is_active'] = False
                return False
            
            # Определяем статус "в работе" с учетом роли и индивидуальных настроек пользователя
            from bot.utils import is_at_work
            user_info = session_data['user_info']
            
            # Получаем роль и индивидуальные настройки рабочей зоны пользователя
            user_role = user_info.get('role')
            user_work_lat = user_info.get('work_latitude')
            user_work_lon = user_info.get('work_longitude')
            user_work_radius = user_info.get('work_radius')
            
            at_work = is_at_work(latitude, longitude, user_role, user_work_lat, user_work_lon, user_work_radius)
            
            # Сохраняем в базу данных (статус "в работе" определяется автоматически)
            location_id = db.add_user_location(
                telegram_id=session_data['telegram_id'],
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                altitude=altitude,
                speed=speed,
                heading=heading
            )
            
            if location_id:
                # Получаем сохраненное местоположение для получения правильного статуса "в работе"
                saved_location = db.get_user_last_location(session_data['telegram_id'])
                at_work = saved_location.get('is_at_work', False) if saved_location else False
                
                # Добавляем в историю сессии
                location_data = {
                    'id': location_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'accuracy': accuracy,
                    'altitude': altitude,
                    'speed': speed,
                    'heading': heading,
                    'is_at_work': at_work,
                    'timestamp': datetime.now().isoformat()
                }
                session_data['locations'].append(location_data)
                
                logger.debug(f"Добавлено местоположение в сессию {session_token}: {latitude}, {longitude}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка добавления местоположения в сессию {session_token}: {e}")
            return False
    
    def stop_session(self, session_token):
        """Остановить сессию отслеживания"""
        try:
            if session_token in self.active_sessions:
                self.active_sessions[session_token]['is_active'] = False
                logger.info(f"Остановлена веб-сессия отслеживания: {session_token}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка остановки сессии {session_token}: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Очистить истекшие сессии"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for token, session_data in self.active_sessions.items():
                if current_time > session_data['expires_at']:
                    expired_sessions.append(token)
            
            for token in expired_sessions:
                del self.active_sessions[token]
                logger.info(f"Удалена истекшая сессия: {token}")
            
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"Ошибка очистки сессий: {e}")
            return 0
    
    def get_active_sessions_info(self):
        """Получить информацию об активных сессиях"""
        try:
            self.cleanup_expired_sessions()
            
            active_info = []
            for token, session_data in self.active_sessions.items():
                if session_data['is_active']:
                    user_info = session_data['user_info']
                    remaining_time = (session_data['expires_at'] - datetime.now()).total_seconds() / 60
                    
                    active_info.append({
                        'session_token': token,
                        'telegram_id': session_data['telegram_id'],
                        'user_name': f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
                        'duration_minutes': session_data['duration_minutes'],
                        'remaining_minutes': max(0, int(remaining_time)),
                        'locations_count': len(session_data['locations']),
                        'created_at': session_data['created_at'].isoformat()
                    })
            
            return active_info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о сессиях: {e}")
            return []

# Глобальный экземпляр трекера
web_tracker = WebLocationTracker()

# Маршруты для веб-отслеживания



@location_web_tracker.route('/api/tracking/<session_token>/location', methods=['POST'])
def update_location(session_token):
    """API для обновления местоположения"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        altitude = data.get('altitude')
        speed = data.get('speed')
        heading = data.get('heading')
        
        if latitude is None or longitude is None:
            return jsonify({'success': False, 'error': 'Latitude and longitude required'}), 400
        
        # Добавляем местоположение в сессию
        success = web_tracker.add_location_to_session(
            session_token, latitude, longitude, accuracy, altitude, speed, heading
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Location updated'})
        else:
            return jsonify({'success': False, 'error': 'Session not found or expired'}), 404
        
    except Exception as e:
        logger.error(f"Ошибка обновления местоположения: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@location_web_tracker.route('/api/tracking/<session_token>/status')
def get_tracking_status(session_token):
    """API для получения статуса отслеживания"""
    try:
        session_info = web_tracker.get_session_info(session_token)
        if not session_info:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Проверяем, не истекла ли сессия
        if datetime.now() > session_info['expires_at']:
            session_info['is_active'] = False
        
        remaining_time = (session_info['expires_at'] - datetime.now()).total_seconds() / 60
        
        return jsonify({
            'success': True,
            'is_active': session_info['is_active'],
            'remaining_minutes': max(0, int(remaining_time)),
            'locations_count': len(session_info['locations']),
            'last_location': session_info['locations'][-1] if session_info['locations'] else None
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса отслеживания: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@location_web_tracker.route('/api/tracking/<session_token>/stop', methods=['POST'])
def stop_tracking(session_token):
    """API для остановки отслеживания"""
    try:
        success = web_tracker.stop_session(session_token)
        
        if success:
            return jsonify({'success': True, 'message': 'Tracking stopped'})
        else:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
    except Exception as e:
        logger.error(f"Ошибка остановки отслеживания: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@location_web_tracker.route('/api/admin/tracking/sessions')
def get_all_sessions():
    """API для получения всех активных сессий (только для администраторов)"""
    try:
        # Здесь должна быть проверка прав администратора
        # Пока возвращаем все сессии
        
        sessions_info = web_tracker.get_active_sessions_info()
        return jsonify({
            'success': True,
            'sessions': sessions_info,
            'total_count': len(sessions_info)
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения сессий: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@location_web_tracker.route('/api/admin/tracking/user/<int:telegram_id>')
def get_user_session(telegram_id):
    """API для получения активной сессии пользователя"""
    try:
        # Проверяем, есть ли активная сессия для пользователя
        for token, session_data in web_tracker.active_sessions.items():
            if (session_data['telegram_id'] == telegram_id and 
                session_data['is_active'] and 
                datetime.now() < session_data['expires_at']):
                
                user_info = session_data['user_info']
                remaining_time = (session_data['expires_at'] - datetime.now()).total_seconds() / 60
                
                return jsonify({
                    'success': True,
                    'has_active_session': True,
                    'session_token': token,
                    'telegram_id': telegram_id,
                    'user_name': f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
                    'remaining_minutes': max(0, int(remaining_time)),
                    'locations_count': len(session_data['locations']),
                    'last_location': session_data['locations'][-1] if session_data['locations'] else None
                })
        
        # Нет активной сессии
        return jsonify({
            'success': True,
            'has_active_session': False,
            'telegram_id': telegram_id
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения сессии пользователя {telegram_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@location_web_tracker.route('/api/admin/tracking/create', methods=['POST'])
def create_tracking_session():
    """API для создания сессии отслеживания (только для администраторов)"""
    try:
        # Здесь должна быть проверка прав администратора
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        telegram_id = data.get('telegram_id')
        duration_minutes = data.get('duration_minutes', 60)
        
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Telegram ID required'}), 400
        
        # Создаем сессию отслеживания
        session_token = web_tracker.create_tracking_session(telegram_id, duration_minutes)
        
        if session_token:
            # Формируем URL для отслеживания
            tracking_url = f"/tracking/{session_token}"
            
            return jsonify({
                'success': True,
                'session_token': session_token,
                'tracking_url': tracking_url,
                'duration_minutes': duration_minutes
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create session'}), 500
        
    except Exception as e:
        logger.error(f"Ошибка создания сессии отслеживания: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 