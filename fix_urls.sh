#!/bin/bash

echo "=== Fixing URL Configuration ==="

cd /opt/driver

# Backup current files
cp urls.py urls.py.backup
cp driver/urls.py driver/urls.py.backup

# Create simple root urls.py
cat > urls.py << 'EOF'
from django.urls import path, include

urlpatterns = [
    path('', include('driver.urls')),
]
EOF

# Create simple driver urls.py
cat > driver/urls.py << 'EOF'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('api/toggle_tracking/', views.toggle_tracking, name='toggle_tracking'),
    path('api/location/', views.get_location, name='get_location'),
]
EOF

echo "URL files updated. Testing Django..."
source venv/bin/activate
python manage.py check

echo "=== URL fix complete ===" 