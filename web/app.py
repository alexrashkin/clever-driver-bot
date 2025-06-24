from flask import Flask, render_template, jsonify, request, redirect, url_for
from config.settings import config
from bot.database import db
from bot.utils import format_distance, format_timestamp, validate_coordinates
import logging

# Настройка логирования
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.WEB_SECRET_KEY

@app.route('/')
def index():
    """Главная страница"""
    try:
        # Получаем данные для дашборда
        tracking_status = db.get_tracking_status()
        last_location = db.get_last_location()
        
        # Получаем настройки с правильными типами
        work_lat_str = db.get_setting('work_latitude', str(config.WORK_LATITUDE))
        work_lon_str = db.get_setting('work_longitude', str(config.WORK_LONGITUDE))
        work_radius_str = db.get_setting('work_radius', str(config.WORK_RADIUS))
        
        # Конвертируем в числа
        work_lat = float(work_lat_str)
        work_lon = float(work_lon_str)
        work_radius = int(work_radius_str)
        
        return render_template('index.html',
                             tracking_status=tracking_status,
                             last_location=last_location,
                             work_lat=work_lat,
                             work_lon=work_lon,
                             work_radius=work_radius)
    except Exception as e:
        logger.error(f"Ошибка при загрузке главной страницы: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/status')
def api_status():
    """API для получения статуса"""
    try:
        tracking_status = db.get_tracking_status()
        last_location = db.get_last_location()
        
        return jsonify({
            'success': True,
            'tracking_active': tracking_status,
            'last_location': last_location
        })
    except Exception as e:
        logger.error(f"Ошибка API статуса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/tracking/toggle', methods=['POST'])
def api_tracking_toggle():
    """API для переключения отслеживания"""
    try:
        current_status = db.get_tracking_status()
        new_status = not current_status
        db.set_tracking_status(new_status)
        
        return jsonify({
            'success': True,
            'active': new_status,
            'message': 'Отслеживание включено' if new_status else 'Отслеживание выключено'
        })
    except Exception as e:
        logger.error(f"Ошибка переключения отслеживания: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/location', methods=['GET'])
def api_location():
    """API для получения последнего местоположения"""
    try:
        last_location = db.get_last_location()
        
        if last_location:
            return jsonify({
                'success': True,
                'location': last_location
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Местоположение не найдено'
            })
    except Exception as e:
        logger.error(f"Ошибка получения местоположения: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/location', methods=['POST'])
def api_location_add():
    """API для добавления местоположения"""
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            return jsonify({'success': False, 'error': 'Координаты обязательны'})
        
        # Валидация координат
        is_valid, error = validate_coordinates(latitude, longitude)
        if not is_valid:
            return jsonify({'success': False, 'error': error})
        
        # Добавляем в базу данных
        db.add_location(latitude, longitude)
        
        return jsonify({'success': True, 'message': 'Местоположение добавлено'})
    except Exception as e:
        logger.error(f"Ошибка добавления местоположения: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history')
def api_history():
    """API для получения истории местоположений"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = db.get_location_history(limit=limit)
        
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings', methods=['GET'])
def api_settings():
    """API для получения настроек"""
    try:
        work_lat = db.get_setting('work_latitude', str(config.WORK_LATITUDE))
        work_lon = db.get_setting('work_longitude', str(config.WORK_LONGITUDE))
        work_radius = db.get_setting('work_radius', str(config.WORK_RADIUS))
        
        return jsonify({
            'success': True,
            'settings': {
                'work_latitude': work_lat,
                'work_longitude': work_lon,
                'work_radius': work_radius
            }
        })
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings', methods=['POST'])
def api_settings_update():
    """API для обновления настроек"""
    try:
        data = request.get_json()
        work_lat = data.get('work_latitude')
        work_lon = data.get('work_longitude')
        work_radius = data.get('work_radius')
        
        if work_lat is not None:
            is_valid, error = validate_coordinates(work_lat, work_lon or config.WORK_LONGITUDE)
            if not is_valid:
                return jsonify({'success': False, 'error': error})
            db.set_setting('work_latitude', work_lat)
        
        if work_lon is not None:
            is_valid, error = validate_coordinates(work_lat or config.WORK_LATITUDE, work_lon)
            if not is_valid:
                return jsonify({'success': False, 'error': error})
            db.set_setting('work_longitude', work_lon)
        
        if work_radius is not None:
            try:
                radius = int(work_radius)
                if radius <= 0:
                    return jsonify({'success': False, 'error': 'Радиус должен быть положительным числом'})
                db.set_setting('work_radius', radius)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Радиус должен быть числом'})
        
        return jsonify({'success': True, 'message': 'Настройки обновлены'})
    except Exception as e:
        logger.error(f"Ошибка обновления настроек: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Внутренняя ошибка сервера'), 500

if __name__ == '__main__':
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=True) 