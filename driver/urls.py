from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('api/toggle_tracking/', views.toggle_tracking, name='toggle_tracking'),
    path('api/location/', views.get_location, name='get_location'),
] 