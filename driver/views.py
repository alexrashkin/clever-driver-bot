from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import TrackingStatus, Location
import json
import math

# Константы для определения местоположения работы
WORK_LATITUDE = 55.676803
WORK_LONGITUDE = 37.52351
WORK_RADIUS = 100  # метров

def calculate_distance(lat1, lon1, lat2, lon2):
    """Вычисление расстояния между двумя точками в метрах"""
    R = 6371000  # радиус Земли в метрах
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def main_page(request):
    """Главная страница приложения"""
    return render(request, 'driver/main.html')

@csrf_exempt
@require_http_methods(["POST"])
def toggle_tracking(request):
    try:
        data = json.loads(request.body)
        is_tracking = data.get('is_tracking', False)
        
        status, created = TrackingStatus.objects.get_or_create(id=1)
        status.is_tracking = is_tracking
        status.save()
        
        return JsonResponse({
            'status': 'success',
            'is_tracking': status.is_tracking
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_location(request):
    try:
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        
        if not latitude or not longitude:
            return JsonResponse({
                'status': 'error',
                'message': 'Both latitude and longitude are required'
            }, status=400)
            
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid latitude or longitude values'
            }, status=400)
        
        # Вычисляем расстояние до работы
        distance = calculate_distance(latitude, longitude, WORK_LATITUDE, WORK_LONGITUDE)
        is_at_work = distance <= WORK_RADIUS
        
        # Save location
        location = Location.objects.create(
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            is_at_work=is_at_work
        )
        
        # Get tracking status
        status = TrackingStatus.objects.get(id=1)
        
        return JsonResponse({
            'status': 'success',
            'is_tracking': status.is_tracking,
            'location': {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'distance': location.distance,
                'is_at_work': location.is_at_work,
                'timestamp': location.timestamp.isoformat()
            }
        })
    except TrackingStatus.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Tracking status not initialized'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 