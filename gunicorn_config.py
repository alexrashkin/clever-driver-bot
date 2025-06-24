import multiprocessing

# Базовые настройки
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Логирование
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Процесс
daemon = True
pidfile = "/var/run/gunicorn/driver.pid"
user = "root"
group = "root"

# Перезапуск
max_requests = 1000
max_requests_jitter = 50
reload = True 