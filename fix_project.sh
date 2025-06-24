#!/bin/bash

cd /opt/driver

# Check Python path
echo "=== Python Path ==="
python3 -c "import sys; print('\n'.join(sys.path))"

# Check Django settings
echo "=== Django Settings ==="
python3 manage.py check

# Check if we can import the app
echo "=== Import Test ==="
python3 -c "from driver.wsgi import application; print('WSGI import successful')"

# Check if we can import the API app
echo "=== API Import Test ==="
python3 -c "from api.views import toggle_tracking; print('API import successful')"

# Check if the database exists and is accessible
echo "=== Database Test ==="
python3 manage.py dbshell << EOF
.tables
.quit
EOF

# Check if static files are collected
echo "=== Static Files ==="
ls -la /opt/static/

# Check if the app is in INSTALLED_APPS
echo "=== INSTALLED_APPS ==="
python3 manage.py shell << EOF
from django.conf import settings
print(settings.INSTALLED_APPS)
EOF

# Check if the app is properly configured
echo "=== App Configuration ==="
python3 manage.py shell << EOF
from django.apps import apps
print(apps.get_app_config('api'))
EOF 