import sqlite3
import os
from datetime import datetime
import logging
from config.settings import config

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path="driver.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Таблица статуса отслеживания
        c.execute('''
            CREATE TABLE IF NOT EXISTS tracking_status (
                id INTEGER PRIMARY KEY,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица местоположений
        c.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                distance REAL,
                is_at_work BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица настроек
        c.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица кодов восстановления пароля
        c.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица пользователей
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id BIGINT UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                login TEXT UNIQUE,
                password_hash TEXT,
                auth_type TEXT DEFAULT 'telegram',
                role TEXT DEFAULT NULL,
                buttons TEXT DEFAULT NULL,
                email TEXT,
                phone TEXT,
                work_latitude REAL,
                work_longitude REAL,
                work_radius INTEGER DEFAULT 100,
                subscription_status TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Вставляем начальный статус (если не существует)
        c.execute('INSERT OR IGNORE INTO tracking_status (id, is_active) VALUES (1, 0)')
        
        # Вставляем настройки по умолчанию (если не существуют)
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', 
                 ('work_latitude', str(config.WORK_LATITUDE)))
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', 
                 ('work_longitude', str(config.WORK_LONGITUDE)))
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', 
                 ('work_radius', str(config.WORK_RADIUS)))
        
        # Миграция: добавляем поле buttons, если его нет
        c.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in c.fetchall()]
        if 'buttons' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN buttons TEXT DEFAULT NULL")
            # Переносим button_name_1/2 в buttons для всех пользователей
            c.execute("SELECT id, button_name_1, button_name_2 FROM users")
            for row in c.fetchall():
                btns = [row[1], row[2]]
                import json
                c.execute("UPDATE users SET buttons = ? WHERE id = ?", (json.dumps(btns, ensure_ascii=False), row[0]))
        
        # Миграция: добавляем поле role, если его нет
        if 'role' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT NULL")
        
        # Миграция: добавляем поля для логин/пароль авторизации
        if 'login' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN login TEXT UNIQUE")
        if 'password_hash' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        if 'auth_type' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN auth_type TEXT DEFAULT 'telegram'")
        
        # Миграция: добавляем поле username, если его нет
        if 'username' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN username TEXT")
        
        # Миграция: добавляем поля email и phone, если их нет
        if 'email' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if 'phone' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        
        # Миграция: удаляем поле recipient_telegram_id, если оно есть (больше не используется)
        if 'recipient_telegram_id' in columns:
            # SQLite не поддерживает DROP COLUMN, поэтому пересоздаем таблицу
            c.execute('''
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                                    first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT NULL,
                buttons TEXT DEFAULT NULL,
                    work_latitude REAL,
                    work_longitude REAL,
                    work_radius INTEGER DEFAULT 100,
                    subscription_status TEXT DEFAULT 'free',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            # Копируем данные (без recipient_telegram_id и устаревших button_name полей)
            c.execute('''
                INSERT INTO users_new 
                (id, telegram_id, username, first_name, last_name, role, 
                 buttons, work_latitude, work_longitude, work_radius, subscription_status, created_at, last_login)
                SELECT id, telegram_id, username, first_name, last_name, role,
                       buttons, work_latitude, work_longitude, work_radius, subscription_status, created_at, last_login
                FROM users
            ''')
            # Удаляем старую таблицу и переименовываем новую
            c.execute('DROP TABLE users')
            c.execute('ALTER TABLE users_new RENAME TO users')
        
        # Миграция: удаляем поля button_name_1 и button_name_2, если они есть (устарели после перехода на buttons)
        c.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in c.fetchall()]
        if 'button_name_1' in columns or 'button_name_2' in columns:
            # Пересоздаем таблицу без устаревших полей
            c.execute('''
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT DEFAULT NULL,
                    buttons TEXT DEFAULT NULL,
                    work_latitude REAL,
                    work_longitude REAL,
                    work_radius INTEGER DEFAULT 100,
                    subscription_status TEXT DEFAULT 'free',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            # Копируем данные (без устаревших button_name полей)
            c.execute('''
                INSERT INTO users_new 
                (id, telegram_id, username, first_name, last_name, role, 
                 buttons, work_latitude, work_longitude, work_radius, subscription_status, created_at, last_login)
                SELECT id, telegram_id, username, first_name, last_name, role,
                       buttons, work_latitude, work_longitude, work_radius, subscription_status, created_at, last_login
                FROM users
            ''')
            # Удаляем старую таблицу и переименовываем новую
            c.execute('DROP TABLE users')
            c.execute('ALTER TABLE users_new RENAME TO users')
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    
    def get_tracking_status(self):
        """Получение статуса отслеживания"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT is_active FROM tracking_status WHERE id = 1')
        result = c.fetchone()
        conn.close()
        return bool(result[0]) if result else False
    
    def set_tracking_status(self, is_active):
        """Установка статуса отслеживания"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE tracking_status 
            SET is_active = ?, last_updated = CURRENT_TIMESTAMP 
            WHERE id = 1
        ''', (1 if is_active else 0,))
        conn.commit()
        conn.close()
        logger.info(f"Статус отслеживания изменен на: {is_active}")
    
    def add_location(self, latitude, longitude, distance=None, is_at_work=False):
        """Добавление записи о местоположении"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO locations (latitude, longitude, distance, is_at_work)
            VALUES (?, ?, ?, ?)
        ''', (latitude, longitude, distance, 1 if is_at_work else 0))
        conn.commit()
        conn.close()
        logger.info(f"Добавлено местоположение: {latitude}, {longitude}")
    
    def get_last_location(self):
        """Получение последнего местоположения"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT latitude, longitude, distance, is_at_work, timestamp
            FROM locations
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'latitude': result[0],
                'longitude': result[1],
                'distance': result[2],
                'is_at_work': bool(result[3]),
                'timestamp': result[4]
            }
        return None
    
    def get_location_history(self, limit=10):
        """Получение истории местоположений"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT latitude, longitude, timestamp, distance, is_at_work
            FROM locations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        history = [{
            'latitude': row[0],
            'longitude': row[1],
            'timestamp': row[2],
            'distance': row[3],
            'is_at_work': bool(row[4])
        } for row in c.fetchall()]
        conn.close()
        return history
    
    def get_history(self, limit=10):
        """Алиас для get_location_history для совместимости"""
        return self.get_location_history(limit)
    
    def get_setting(self, key, default=None):
        """Получение настройки"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else default
    
    def set_setting(self, key, value):
        """Установка настройки"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, str(value)))
        conn.commit()
        conn.close()
        logger.info(f"Настройка {key} изменена на: {value}")
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        return sqlite3.connect(self.db_path)

    def create_user(self, telegram_id, username=None, first_name=None, last_name=None):
        """Создать нового пользователя"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        import json
        default_buttons = json.dumps([
            '📍 Еду на работу',
            '🚗 Подъезжаю к дому'
        ], ensure_ascii=False)
        c.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name, buttons)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            telegram_id, username, first_name, last_name,
            default_buttons
        ))
        conn.commit()
        conn.close()
        logger.info(f"Создан пользователь telegram_id={telegram_id}")

    def get_user_by_telegram_id(self, telegram_id):
        """Получить пользователя по telegram_id"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT * FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        row = c.fetchone()
        columns = [desc[0] for desc in c.description]
        conn.close()
        if row:
            user = dict(zip(columns, row))
            import json
            try:
                user['buttons'] = json.loads(user['buttons']) if user['buttons'] else []
            except Exception:
                user['buttons'] = []
            return user
        return None

    def get_user_by_id(self, user_id):
        """Получить пользователя по ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT * FROM users WHERE id = ?
        ''', (user_id,))
        row = c.fetchone()
        columns = [desc[0] for desc in c.description]
        conn.close()
        if row:
            user = dict(zip(columns, row))
            import json
            try:
                user['buttons'] = json.loads(user['buttons']) if user['buttons'] else []
            except Exception:
                user['buttons'] = []
            return user
        return None

    def get_user_role(self, telegram_id):
        """Получить роль пользователя"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT role FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        result = c.fetchone()
        conn.close()
        role = result[0] if result else None
        logger.info(f"DATABASE: get_user_role({telegram_id}) = {role}")
        return role
    
    def set_user_role(self, telegram_id, role):
        """Установить роль пользователя (admin, driver, recipient)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE users SET role = ? WHERE telegram_id = ?
        ''', (role, telegram_id))
        conn.commit()
        conn.close()
        logger.info(f"Роль пользователя {telegram_id} установлена как: {role}")
    
    def is_recipient_only(self, telegram_id):
        """Проверить, является ли пользователь только получателем уведомлений"""
        role = self.get_user_role(telegram_id)
        return role == 'recipient'
    
    def create_user_with_login(self, login, password, first_name=None, last_name=None, role='driver', email=None, phone=None):
        """Создать пользователя с логином и паролем"""
        import hashlib
        import secrets
        import json
        
        # Хешируем пароль с солью
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        password_hash_hex = salt + password_hash.hex()
        
        # Дефолтные кнопки
        default_buttons = json.dumps([
            '📍 Еду на работу',
            '🚗 Подъезжаю к дому'
        ], ensure_ascii=False)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO users (login, password_hash, first_name, last_name, auth_type, role, buttons, email, phone)
                VALUES (?, ?, ?, ?, 'login', ?, ?, ?, ?)
            ''', (login, password_hash_hex, first_name, last_name, role, default_buttons, email, phone))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            logger.info(f"Создан пользователь с логином: {login}")
            return True, user_id
        except sqlite3.IntegrityError as e:
            conn.close()
            return False, f"Ошибка создания пользователя: {e}"
    
    def get_user_by_login(self, login):
        """Получить пользователя по логину"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Исключаем NULL значения из поиска
        c.execute('''
            SELECT * FROM users WHERE login = ? AND login IS NOT NULL
        ''', (login,))
        row = c.fetchone()
        columns = [desc[0] for desc in c.description]
        conn.close()
        if row:
            user = dict(zip(columns, row))
            import json
            try:
                user['buttons'] = json.loads(user['buttons']) if user['buttons'] else []
            except Exception:
                user['buttons'] = []
            return user
        return None
    
    def verify_password(self, login, password):
        """Проверить пароль пользователя"""
        user = self.get_user_by_login(login)
        if not user or not user.get('password_hash'):
            return False
        
        import hashlib
        password_hash_hex = user['password_hash']
        salt = password_hash_hex[:32]  # Первые 32 символа - это соль
        stored_hash = password_hash_hex[32:]  # Остальное - хеш
        
        # Хешируем введенный пароль с той же солью
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        return computed_hash.hex() == stored_hash
    
    def get_user_role_by_login(self, login):
        """Получить роль пользователя по логину"""
        user = self.get_user_by_login(login)
        return user.get('role') if user else None
    
    def get_all_users(self):
        """Получить всех пользователей для администрирования"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT id, telegram_id, login, first_name, last_name, auth_type, role, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        rows = c.fetchall()
        columns = [desc[0] for desc in c.description]
        conn.close()
        
        users = []
        for row in rows:
            user = dict(zip(columns, row))
            users.append(user)
        return users
    
    def delete_user_by_id(self, user_id):
        """Удалить пользователя по ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        if deleted:
            logger.info(f"Пользователь с ID {user_id} удален")
        return deleted

    def update_user_settings(self, telegram_id, **kwargs):
        """Обновить настройки пользователя по telegram_id (имена кнопок, радиус, координаты)"""
        if not kwargs:
            return
        # Устаревшая логика button_name_1/2 удалена - теперь используется только buttons массив
        # Сериализация массива кнопок
        if 'buttons' in kwargs and isinstance(kwargs['buttons'], list):
            import json
            kwargs['buttons'] = json.dumps(kwargs['buttons'], ensure_ascii=False)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(telegram_id)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE telegram_id = ?"
        c.execute(sql, values)
        conn.commit()
        conn.close()
        logger.info(f"Обновлены настройки пользователя telegram_id={telegram_id}: {kwargs}")

    def update_user_settings_by_login(self, login, **kwargs):
        """Обновить настройки пользователя по логину (имена кнопок, радиус, координаты)"""
        if not kwargs:
            return
        # Сериализация массива кнопок
        if 'buttons' in kwargs and isinstance(kwargs['buttons'], list):
            import json
            kwargs['buttons'] = json.dumps(kwargs['buttons'], ensure_ascii=False)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(login)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE login = ?"
        c.execute(sql, values)
        conn.commit()
        conn.close()
        logger.info(f"Обновлены настройки пользователя login={login}: {kwargs}")

    def bind_telegram_to_user(self, login, telegram_id, username=None, first_name=None, last_name=None):
        """Привязать Telegram ID к существующему пользователю по логину"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Проверяем, что пользователь с таким логином существует
        user = self.get_user_by_login(login)
        if not user:
            conn.close()
            return False, "Пользователь с таким логином не найден"
        
        # Проверяем, что Telegram ID не занят другим пользователем
        existing_telegram_user = self.get_user_by_telegram_id(telegram_id)
        if existing_telegram_user and existing_telegram_user.get('login') != login:
            conn.close()
            return False, "Этот Telegram аккаунт уже привязан к другому пользователю"
        
        # Обновляем пользователя
        c.execute('''
            UPDATE users 
            SET telegram_id = ?, username = ?, first_name = ?, last_name = ?, auth_type = 'hybrid'
            WHERE login = ?
        ''', (telegram_id, username, first_name, last_name, login))
        
        conn.commit()
        conn.close()
        logger.info(f"Telegram ID {telegram_id} привязан к пользователю {login}")
        return True, "Telegram аккаунт успешно привязан"

    def unbind_telegram_from_user(self, login_or_id):
        """Отвязать Telegram аккаунт от пользователя по логину или ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Определяем, что передано - логин или ID
        if isinstance(login_or_id, int) or (isinstance(login_or_id, str) and login_or_id.isdigit()):
            # Это ID
            user_id = int(login_or_id)
            user = self.get_user_by_id(user_id)
            where_clause = "id = ?"
            where_value = user_id
        else:
            # Это логин
            user = self.get_user_by_login(login_or_id)
            where_clause = "login = ?"
            where_value = login_or_id
        
        if not user:
            conn.close()
            return False, f"Пользователь не найден: {login_or_id}"
        
        # Проверяем, что у пользователя есть привязанный Telegram
        if not user.get('telegram_id'):
            conn.close()
            return False, "У пользователя нет привязанного Telegram аккаунта"
        
        # Отвязываем Telegram (устанавливаем telegram_id = NULL)
        c.execute(f'''
            UPDATE users 
            SET telegram_id = NULL, username = NULL, first_name = NULL, last_name = NULL, auth_type = 'login'
            WHERE {where_clause}
        ''', (where_value,))
        
        conn.commit()
        conn.close()
        logger.info(f"Telegram аккаунт отвязан от пользователя {login_or_id}")
        return True, "Telegram аккаунт успешно отвязан"

    def create_password_reset_code(self, login):
        """Создать код восстановления пароля для пользователя"""
        import secrets
        from datetime import datetime, timedelta
        
        # Проверяем, что пользователь существует
        user = self.get_user_by_login(login)
        if not user:
            return False, "Пользователь с таким логином не найден"
        
        # Генерируем код
        code = secrets.token_hex(3).upper()  # 6 символов
        
        # Устанавливаем время истечения (1 час)
        expires_at = datetime.now() + timedelta(hours=1)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Удаляем старые коды для этого пользователя
        c.execute('DELETE FROM password_reset_codes WHERE login = ?', (login,))
        
        # Создаем новый код
        c.execute('''
            INSERT INTO password_reset_codes (login, code, expires_at)
            VALUES (?, ?, ?)
        ''', (login, code, expires_at))
        
        conn.commit()
        conn.close()
        
        # Пытаемся отправить код через Telegram, если у пользователя есть telegram_id
        telegram_id = user.get('telegram_id')
        if telegram_id:
            try:
                from config.settings import config
                import requests
                
                message = f"🔐 Код восстановления пароля: {code}\n\nЭтот код действителен 1 час.\nЕсли вы не запрашивали восстановление пароля, проигнорируйте это сообщение."
                
                url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
                data = {
                    'chat_id': telegram_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, data=data, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Код восстановления отправлен в Telegram для пользователя {login}")
                    return True, "Код отправлен в Telegram"
                else:
                    logger.warning(f"Не удалось отправить код в Telegram для {login}: {response.text}")
            except Exception as e:
                logger.error(f"Ошибка отправки кода в Telegram для {login}: {e}")
        
        # Пытаемся отправить код через Email, если у пользователя есть email
        email = user.get('email')
        if email:
            try:
                from bot.email_utils import send_password_reset_email
                
                if send_password_reset_email(email, login, code):
                    logger.info(f"Код восстановления отправлен на email для пользователя {login}")
                    return True, "Код отправлен на email"
                else:
                    logger.warning(f"Не удалось отправить код на email для {login}")
            except Exception as e:
                logger.error(f"Ошибка отправки кода на email для {login}: {e}")
        
        # Если нет способов отправки, возвращаем ошибку
        logger.warning(f"Нет доступных способов отправки кода для пользователя {login}")
        return False, "Для восстановления пароля необходимо иметь привязанный Telegram аккаунт или email"

    def verify_password_reset_code(self, login, code):
        """Проверить код восстановления пароля"""
        from datetime import datetime
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, expires_at, used FROM password_reset_codes 
            WHERE login = ? AND code = ?
        ''', (login, code))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            return False, "Код не найден"
        
        reset_id, expires_at, used = result
        
        if used:
            return False, "Код уже использован"
        
        # Проверяем срок действия
        expires_datetime = datetime.fromisoformat(expires_at)
        if datetime.now() > expires_datetime:
            return False, "Код истек"
        
        return True, reset_id

    def mark_reset_code_used(self, reset_id):
        """Отметить код восстановления как использованный"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('UPDATE password_reset_codes SET used = 1 WHERE id = ?', (reset_id,))
        conn.commit()
        conn.close()

    def reset_user_password(self, login, new_password):
        """Сбросить пароль пользователя"""
        import hashlib
        import secrets
        
        # Хешируем новый пароль
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000)
        password_hash_hex = salt + password_hash.hex()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            UPDATE users 
            SET password_hash = ?, auth_type = 'login'
            WHERE login = ?
        ''', (password_hash_hex, login))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Пароль пользователя {login} сброшен")
        return True

# Создаем глобальный экземпляр базы данных
db = Database()
