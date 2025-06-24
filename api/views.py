from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import TrackingStatus, Location
import json

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
        
        # Save location
        location = Location.objects.create(
            latitude=latitude,
            longitude=longitude
        )
        
        # Get tracking status
        status = TrackingStatus.objects.get(id=1)
        
        return JsonResponse({
            'status': 'success',
            'is_tracking': status.is_tracking,
            'location': {
                'latitude': location.latitude,
                'longitude': location.longitude,
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