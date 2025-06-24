#!/bin/bash

# Create project directory
mkdir -p /opt/driver
cd /opt/driver

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install django djangorestframework gunicorn

# Create Django project
django-admin startproject driver .
python manage.py startapp api

# Create necessary directories
mkdir -p /opt/static
mkdir -p /var/log/gunicorn
mkdir -p /var/run/gunicorn

# Create settings.py
cat > driver/settings.py << 'EOL'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = False
ALLOWED_HOSTS = ['194.87.236.174']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'driver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'driver.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = '/opt/static'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}
EOL

# Create models.py
cat > api/models.py << 'EOL'
from django.db import models

class TrackingStatus(models.Model):
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tracking {'Active' if self.is_active else 'Inactive'}"

class Location(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    distance = models.FloatField()
    is_at_work = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Location at {self.latitude}, {self.longitude}"
EOL

# Create views.py
cat > api/views.py << 'EOL'
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import TrackingStatus, Location
import math

WORK_LATITUDE = 55.676803
WORK_LONGITUDE = 37.52351
WORK_RADIUS = 100

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@api_view(['POST'])
def toggle_tracking(request):
    status = get_object_or_404(TrackingStatus, id=1)
    status.is_active = not status.is_active
    status.save()
    return Response({'active': status.is_active})

@api_view(['GET'])
def get_location(request):
    try:
        latitude = float(request.GET.get('latitude', 0))
        longitude = float(request.GET.get('longitude', 0))
    except (TypeError, ValueError):
        return Response({'error': 'Invalid coordinates'}, status=400)

    distance = calculate_distance(latitude, longitude, WORK_LATITUDE, WORK_LONGITUDE)
    is_at_work = distance <= WORK_RADIUS

    location = Location.objects.create(
        latitude=latitude,
        longitude=longitude,
        distance=distance,
        is_at_work=is_at_work
    )

    return Response({
        'success': True,
        'location': {
            'latitude': location.latitude,
            'longitude': location.longitude,
            'distance': location.distance,
            'is_at_work': location.is_at_work,
            'timestamp': location.timestamp
        }
    })
EOL

# Create urls.py
cat > api/urls.py << 'EOL'
from django.urls import path
from . import views

urlpatterns = [
    path('toggle_tracking/', views.toggle_tracking, name='toggle_tracking'),
    path('location/', views.get_location, name='get_location'),
]
EOL

# Create main urls.py
cat > driver/urls.py << 'EOL'
from django.urls import path, include

urlpatterns = [
    path('api/', include('api.urls')),
]
EOL

# Create gunicorn config
cat > gunicorn_config.py << 'EOL'
bind = "127.0.0.1:8000"
workers = 4
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
capture_output = True
daemon = True
pidfile = "/var/run/gunicorn/gunicorn.pid"
max_requests = 1000
max_requests_jitter = 50
EOL

# Create nginx config
cat > /etc/nginx/conf.d/driver.conf << 'EOL'
server {
    listen 80;
    server_name 194.87.236.174;

    access_log /var/log/nginx/driver.access.log;
    error_log /var/log/nginx/driver.error.log;

    client_max_body_size 100M;

    location /static/ {
        alias /opt/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOL

# Create systemd service
cat > /etc/systemd/system/driver.service << 'EOL'
[Unit]
Description=Driver API Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/driver
Environment="PATH=/opt/driver/venv/bin"
ExecStart=/opt/driver/venv/bin/gunicorn -c gunicorn_config.py driver.wsgi:application

[Install]
WantedBy=multi-user.target
EOL

# Apply migrations and collect static files
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Create initial tracking status
python manage.py shell << 'EOL'
from api.models import TrackingStatus
TrackingStatus.objects.create(id=1, is_active=False)
EOL

# Set permissions
chown -R root:root /opt/driver
chown -R root:root /opt/static
chmod -R 755 /opt/driver
chmod -R 755 /opt/static

# Restart services
systemctl daemon-reload
systemctl restart nginx
systemctl restart driver 