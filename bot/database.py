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
        
        # Таблица приглашений получателей уведомлений
        c.execute('''
            CREATE TABLE IF NOT EXISTS invitations (
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
        
        # Таблица логов уведомлений
        c.execute('''
            CREATE TABLE IF NOT EXISTS notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                sender_id INTEGER,
                sender_telegram_id BIGINT,
                sender_login TEXT,
                notification_text TEXT NOT NULL,
                recipients_count INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                confirmation_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица деталей отправки уведомлений
        c.execute('''
            CREATE TABLE IF NOT EXISTS notification_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_log_id INTEGER NOT NULL,
                recipient_telegram_id BIGINT NOT NULL,
                recipient_name TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (notification_log_id) REFERENCES notification_logs (id)
            )
        ''')
        
        # Таблица местоположений пользователей
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                telegram_id BIGINT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL,
                altitude REAL,
                speed REAL,
                heading REAL,
                is_at_work BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
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
            SELECT id, telegram_id, login, first_name, last_name, auth_type, role, created_at, last_login, email, phone, password_hash
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
        
        # Отправляем код через Email (обязательно для всех пользователей)
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
        
        # Если нет email, возвращаем ошибку
        logger.warning(f"У пользователя {login} не указан email")
        return False, "Для восстановления пароля необходим email, указанный при регистрации"

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
    
    def create_invitation(self, inviter_id, invite_code):
        """Создать приглашение получателя уведомлений"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Получаем информацию о приглашающем
        inviter = self.get_user_by_id(inviter_id)
        if not inviter:
            conn.close()
            return False, "Приглашающий пользователь не найден"
        
        try:
            c.execute('''
                INSERT INTO invitations (inviter_id, inviter_telegram_id, inviter_login, invite_code, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (inviter_id, inviter.get('telegram_id'), inviter.get('login'), invite_code))
            
            conn.commit()
            conn.close()
            logger.info(f"Создано приглашение: {invite_code} от пользователя {inviter_id}")
            return True, "Приглашение создано"
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка создания приглашения: {e}")
            return False, "Ошибка создания приглашения"
    
    def get_invitation_by_code(self, invite_code):
        """Получить приглашение по коду"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, inviter_id, inviter_telegram_id, inviter_login, invite_code, 
                   status, recipient_telegram_id, recipient_username, recipient_first_name, 
                   recipient_last_name, created_at, accepted_at
            FROM invitations 
            WHERE invite_code = ?
        ''', (invite_code,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'inviter_id', 'inviter_telegram_id', 'inviter_login', 'invite_code',
                      'status', 'recipient_telegram_id', 'recipient_username', 'recipient_first_name',
                      'recipient_last_name', 'created_at', 'accepted_at']
            return dict(zip(columns, row))
        return None
    
    def accept_invitation(self, invite_code, recipient_telegram_id, recipient_username=None, 
                         recipient_first_name=None, recipient_last_name=None):
        """Принять приглашение"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE invitations 
                SET status = 'accepted', recipient_telegram_id = ?, recipient_username = ?,
                    recipient_first_name = ?, recipient_last_name = ?, accepted_at = CURRENT_TIMESTAMP
                WHERE invite_code = ? AND status = 'pending'
            ''', (recipient_telegram_id, recipient_username, recipient_first_name, 
                  recipient_last_name, invite_code))
            
            updated = c.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                logger.info(f"Приглашение {invite_code} принято пользователем {recipient_telegram_id}")
            return updated
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка принятия приглашения: {e}")
            return False
    
    def get_user_invitations(self, user_id):
        """Получить все приглашения пользователя (как приглашающего)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, inviter_id, inviter_telegram_id, inviter_login, invite_code, 
                   status, recipient_telegram_id, recipient_username, recipient_first_name, 
                   recipient_last_name, created_at, accepted_at
            FROM invitations 
            WHERE inviter_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            columns = ['id', 'inviter_id', 'inviter_telegram_id', 'inviter_login', 'invite_code',
                      'status', 'recipient_telegram_id', 'recipient_username', 'recipient_first_name',
                      'recipient_last_name', 'created_at', 'accepted_at']
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_all_invitations(self):
        """Получить все приглашения для админ-панели"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT i.id, i.inviter_id, i.inviter_telegram_id, i.inviter_login, i.invite_code, 
                   i.status, i.recipient_telegram_id, i.recipient_username, i.recipient_first_name, 
                   i.recipient_last_name, i.created_at, i.accepted_at,
                   u1.first_name as inviter_first_name, u1.last_name as inviter_last_name,
                   u2.first_name as recipient_first_name_full, u2.last_name as recipient_last_name_full
            FROM invitations i
            LEFT JOIN users u1 ON i.inviter_id = u1.id
            LEFT JOIN users u2 ON i.recipient_telegram_id = u2.telegram_id
            ORDER BY i.created_at DESC
        ''')
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            columns = ['id', 'inviter_id', 'inviter_telegram_id', 'inviter_login', 'invite_code',
                      'status', 'recipient_telegram_id', 'recipient_username', 'recipient_first_name',
                      'recipient_last_name', 'created_at', 'accepted_at', 'inviter_first_name',
                      'inviter_last_name', 'recipient_first_name_full', 'recipient_last_name_full']
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def delete_invitation(self, invitation_id):
        """Удалить приглашение по ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Получаем информацию о приглашении перед удалением
            c.execute('SELECT invite_code, status FROM invitations WHERE id = ?', (invitation_id,))
            invitation = c.fetchone()
            
            if not invitation:
                conn.close()
                return False, "Приглашение не найдено"
            
            invite_code, status = invitation
            
            # Удаляем приглашение
            c.execute('DELETE FROM invitations WHERE id = ?', (invitation_id,))
            deleted = c.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"Приглашение {invite_code} (статус: {status}) удалено администратором")
                return True, f"Приглашение {invite_code} удалено"
            else:
                return False, "Ошибка удаления приглашения"
                
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка удаления приглашения {invitation_id}: {e}")
            return False, f"Ошибка удаления: {e}"

    # Методы для системы подтверждений уведомлений
    
    def create_notification_log(self, notification_type, sender_id=None, sender_telegram_id=None, 
                               sender_login=None, notification_text=""):
        """Создать запись в логе уведомлений"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO notification_logs 
                (notification_type, sender_id, sender_telegram_id, sender_login, notification_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (notification_type, sender_id, sender_telegram_id, sender_login, notification_text))
            
            notification_log_id = c.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Создан лог уведомления ID: {notification_log_id}, тип: {notification_type}")
            return notification_log_id
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка создания лога уведомления: {e}")
            return None
    
    def add_notification_detail(self, notification_log_id, recipient_telegram_id, 
                               recipient_name=None, status="pending", error_message=None):
        """Добавить деталь отправки уведомления"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO notification_details 
                (notification_log_id, recipient_telegram_id, recipient_name, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (notification_log_id, recipient_telegram_id, recipient_name, status, error_message))
            
            detail_id = c.lastrowid
            conn.commit()
            conn.close()
            
            return detail_id
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка добавления детали уведомления: {e}")
            return None
    
    def update_notification_detail(self, notification_log_id, recipient_telegram_id, 
                                  status, error_message=None):
        """Обновить статус отправки уведомления"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE notification_details 
                SET status = ?, error_message = ?, sent_at = CURRENT_TIMESTAMP
                WHERE notification_log_id = ? AND recipient_telegram_id = ?
            ''', (status, error_message, notification_log_id, recipient_telegram_id))
            
            updated = c.rowcount > 0
            conn.commit()
            conn.close()
            
            return updated
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка обновления детали уведомления: {e}")
            return False
    
    def complete_notification_log(self, notification_log_id, sent_count, failed_count):
        """Завершить лог уведомления с итоговой статистикой"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE notification_logs 
                SET sent_count = ?, failed_count = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (sent_count, failed_count, notification_log_id))
            
            updated = c.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                logger.info(f"Завершен лог уведомления ID: {notification_log_id}, отправлено: {sent_count}, ошибок: {failed_count}")
            return updated
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка завершения лога уведомления: {e}")
            return False
    
    def mark_confirmation_sent(self, notification_log_id):
        """Отметить, что подтверждение отправлено"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE notification_logs 
                SET confirmation_sent = 1
                WHERE id = ?
            ''', (notification_log_id,))
            
            updated = c.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                logger.info(f"Подтверждение отправлено для лога уведомления ID: {notification_log_id}")
            return updated
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка отметки подтверждения: {e}")
            return False
    
    def get_notification_log(self, notification_log_id):
        """Получить лог уведомления по ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, notification_type, sender_id, sender_telegram_id, sender_login,
                   notification_text, recipients_count, sent_count, failed_count,
                   confirmation_sent, created_at, completed_at
            FROM notification_logs 
            WHERE id = ?
        ''', (notification_log_id,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'notification_type', 'sender_id', 'sender_telegram_id', 'sender_login',
                      'notification_text', 'recipients_count', 'sent_count', 'failed_count',
                      'confirmation_sent', 'created_at', 'completed_at']
            return dict(zip(columns, row))
        return None
    
    def get_notification_details(self, notification_log_id):
        """Получить детали отправки уведомления"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, notification_log_id, recipient_telegram_id, recipient_name,
                   status, error_message, sent_at
            FROM notification_details 
            WHERE notification_log_id = ?
            ORDER BY sent_at
        ''', (notification_log_id,))
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            columns = ['id', 'notification_log_id', 'recipient_telegram_id', 'recipient_name',
                      'status', 'error_message', 'sent_at']
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_recent_notifications(self, limit=10):
        """Получить последние уведомления"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT nl.id, nl.notification_type, nl.sender_telegram_id, nl.sender_login,
                   nl.notification_text, nl.recipients_count, nl.sent_count, nl.failed_count,
                   nl.confirmation_sent, nl.created_at, nl.completed_at,
                   u.first_name, u.last_name
            FROM notification_logs nl
            LEFT JOIN users u ON nl.sender_id = u.id
            ORDER BY nl.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            columns = ['id', 'notification_type', 'sender_telegram_id', 'sender_login',
                      'notification_text', 'recipients_count', 'sent_count', 'failed_count',
                      'confirmation_sent', 'created_at', 'completed_at', 'sender_first_name', 'sender_last_name']
            return [dict(zip(columns, row)) for row in rows]
        return []

    # Методы для работы с местоположениями пользователей
    
    def add_user_location(self, telegram_id, latitude, longitude, accuracy=None, 
                         altitude=None, speed=None, heading=None, is_at_work=None):
        """Добавить местоположение пользователя"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Получаем user_id по telegram_id
            user_info = self.get_user_by_telegram_id(telegram_id)
            if not user_info:
                conn.close()
                return False
            
            # Если статус "в работе" не передан, определяем автоматически с учетом роли
            if is_at_work is None:
                from bot.utils import is_at_work
                user_role = user_info.get('role')
                user_work_lat = user_info.get('work_latitude')
                user_work_lon = user_info.get('work_longitude')
                user_work_radius = user_info.get('work_radius')
                is_at_work = is_at_work(latitude, longitude, user_role, user_work_lat, user_work_lon, user_work_radius)
            
            c.execute('''
                INSERT INTO user_locations 
                (user_id, telegram_id, latitude, longitude, accuracy, altitude, speed, heading, is_at_work)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_info['id'], telegram_id, latitude, longitude, accuracy, altitude, speed, heading, is_at_work))
            
            location_id = c.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Местоположение пользователя {telegram_id} добавлено: {latitude}, {longitude}")
            return location_id
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка добавления местоположения пользователя {telegram_id}: {e}")
            return False
    
    def get_user_last_location(self, telegram_id):
        """Получить последнее местоположение пользователя"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT ul.id, ul.user_id, ul.telegram_id, ul.latitude, ul.longitude,
                   ul.accuracy, ul.altitude, ul.speed, ul.heading, ul.is_at_work, ul.created_at,
                   u.first_name, u.last_name, u.username, u.role,
                   u.work_latitude, u.work_longitude, u.work_radius
            FROM user_locations ul
            JOIN users u ON ul.user_id = u.id
            WHERE ul.telegram_id = ?
            ORDER BY ul.created_at DESC
            LIMIT 1
        ''', (telegram_id,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'user_id', 'telegram_id', 'latitude', 'longitude',
                      'accuracy', 'altitude', 'speed', 'heading', 'is_at_work', 'created_at',
                      'first_name', 'last_name', 'username', 'role',
                      'work_latitude', 'work_longitude', 'work_radius']
            location_data = dict(zip(columns, row))
            
            # Вычисляем расстояние до работы
            from bot.utils import calculate_distance
            if location_data['work_latitude'] and location_data['work_longitude']:
                distance = calculate_distance(
                    location_data['latitude'], location_data['longitude'],
                    location_data['work_latitude'], location_data['work_longitude']
                )
            else:
                from config.settings import config
                distance = calculate_distance(
                    location_data['latitude'], location_data['longitude'],
                    config.WORK_LATITUDE, config.WORK_LONGITUDE
                )
            
            location_data['distance_to_work'] = distance
            return location_data
        return None
    
    def get_user_location_history(self, telegram_id, limit=10):
        """Получить историю местоположений пользователя"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT ul.id, ul.user_id, ul.telegram_id, ul.latitude, ul.longitude,
                   ul.accuracy, ul.altitude, ul.speed, ul.heading, ul.is_at_work, ul.created_at,
                   u.first_name, u.last_name, u.username
            FROM user_locations ul
            JOIN users u ON ul.user_id = u.id
            WHERE ul.telegram_id = ?
            ORDER BY ul.created_at DESC
            LIMIT ?
        ''', (telegram_id, limit))
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            columns = ['id', 'user_id', 'telegram_id', 'latitude', 'longitude',
                      'accuracy', 'altitude', 'speed', 'heading', 'is_at_work', 'created_at',
                      'first_name', 'last_name', 'username']
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_recipient_locations(self, limit=50):
        """Получить последние местоположения всех получателей уведомлений"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT ul.id, ul.user_id, ul.telegram_id, ul.latitude, ul.longitude,
                   ul.accuracy, ul.altitude, ul.speed, ul.heading, ul.is_at_work, ul.created_at,
                   u.first_name, u.last_name, u.username, u.role
            FROM user_locations ul
            JOIN users u ON ul.user_id = u.id
            WHERE u.role = 'recipient' AND ul.telegram_id IS NOT NULL
            AND ul.id = (
                SELECT MAX(ul2.id) 
                FROM user_locations ul2 
                WHERE ul2.telegram_id = ul.telegram_id
            )
            ORDER BY ul.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        if rows:
            columns = ['id', 'user_id', 'telegram_id', 'latitude', 'longitude',
                      'accuracy', 'altitude', 'speed', 'heading', 'is_at_work', 'created_at',
                      'first_name', 'last_name', 'username', 'role']
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_user_by_telegram_id_with_location(self, telegram_id):
        """Получить информацию о пользователе с последним местоположением"""
        user_info = self.get_user_by_telegram_id(telegram_id)
        if not user_info:
            return None
        
        last_location = self.get_user_last_location(telegram_id)
        user_info['last_location'] = last_location
        
        return user_info
    
    def fix_recipient_locations(self):
        """Исправить статус is_at_work для всех получателей (должен быть False)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Обновляем все записи получателей, устанавливая is_at_work = False
            c.execute('''
                UPDATE user_locations 
                SET is_at_work = 0 
                WHERE user_id IN (
                    SELECT id FROM users WHERE role = 'recipient'
                )
            ''')
            
            updated_count = c.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Исправлено {updated_count} записей местоположений получателей")
            return updated_count
            
        except Exception as e:
            conn.close()
            logger.error(f"Ошибка исправления записей получателей: {e}")
            return 0

# Создаем глобальный экземпляр базы данных
db = Database()
