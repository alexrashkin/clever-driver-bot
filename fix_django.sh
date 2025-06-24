#!/bin/bash

cd /opt/driver

# Activate virtual environment
source venv/bin/activate

# Update settings.py
cat > driver/settings.py << 'EOL'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = True  # Enable debug mode temporarily
ALLOWED_HOSTS = ['*']  # Allow all hosts temporarily

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
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ],
}
EOL

# Update urls.py
cat > driver/urls.py << 'EOL'
from django.urls import path, include

urlpatterns = [
    path('api/', include('api.urls')),
]
EOL

# Update api/urls.py
cat > api/urls.py << 'EOL'
from django.urls import path
from . import views

urlpatterns = [
    path('toggle_tracking/', views.toggle_tracking, name='toggle_tracking'),
    path('location/', views.get_location, name='get_location'),
]
EOL

# Update api/views.py
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
    status, created = TrackingStatus.objects.get_or_create(id=1, defaults={'is_active': False})
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

# Apply migrations
python3 manage.py makemigrations
python3 manage.py migrate

# Create initial tracking status
python3 manage.py shell << EOF
from api.models import TrackingStatus
TrackingStatus.objects.get_or_create(id=1, defaults={'is_active': False})
EOF

# Restart service
systemctl restart driver

# Test API
echo "=== Testing API ==="
curl -X POST http://localhost:8000/api/toggle_tracking/
echo
curl "http://localhost:8000/api/location/?latitude=55.676803&longitude=37.52351" 