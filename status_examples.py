#!/usr/bin/env python3
"""
ДЕМОНСТРАЦИЯ РАБОТЫ СТАТУСА АВТОМОБИЛЯ
Показывает как определяется статус для разных координат
"""

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Расчет расстояния по формуле гаверсинуса"""
    R = 6371000  # Радиус Земли в метрах
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_status(latitude, longitude):
    """Определение статуса по координатам"""
    WORK_LAT = 55.676803
    WORK_LON = 37.523510
    WORK_RADIUS = 100  # метров
    
    distance = calculate_distance(latitude, longitude, WORK_LAT, WORK_LON)
    is_at_work = distance <= WORK_RADIUS
    
    return {
        'distance': round(distance, 1),
        'is_at_work': is_at_work,
        'status': '🟢 ВОДИТЕЛЬ ОЖИДАЕТ' if is_at_work else '🟡 В ПУТИ'
    }

def demo_status_examples():
    """Демонстрация примеров статусов"""
    print("🎯 ДЕМОНСТРАЦИЯ РАБОТЫ СТАТУСА")
    print("=" * 50)
    
    # Примеры различных координат
    test_locations = [
        {
            'name': '🏢 Точно в центре рабочей зоны',
            'lat': 55.676803, 'lon': 37.523510,
            'expected': 'ВОДИТЕЛЬ ОЖИДАЕТ'
        },
        {
            'name': '🎯 На границе зоны (50м от центра)',
            'lat': 55.677253, 'lon': 37.523960,
            'expected': 'ВОДИТЕЛЬ ОЖИДАЕТ'
        },
        {
            'name': '⚠️ На самой границе (100м от центра)',
            'lat': 55.677703, 'lon': 37.523510,
            'expected': 'ВОДИТЕЛЬ ОЖИДАЕТ (граница)'
        },
        {
            'name': '🚗 Чуть за границей (110м от центра)',
            'lat': 55.677793, 'lon': 37.523510,
            'expected': 'В ПУТИ'
        },
        {
            'name': '🏠 Красная площадь (далеко)',
            'lat': 55.7539, 'lon': 37.6208,
            'expected': 'В ПУТИ'
        },
        {
            'name': '🏢 Москва-Сити (далеко)',
            'lat': 55.7504, 'lon': 37.5384,
            'expected': 'В ПУТИ'
        }
    ]
    
    print("📍 ПРИМЕРЫ ОПРЕДЕЛЕНИЯ СТАТУСА:\n")
    
    for i, location in enumerate(test_locations, 1):
        result = get_status(location['lat'], location['lon'])
        
        print(f"{i}. {location['name']}")
        print(f"   📍 Координаты: {location['lat']:.6f}, {location['lon']:.6f}")
        print(f"   📏 Расстояние: {result['distance']} м")
        print(f"   🎯 Статус: {result['status']}")
        print(f"   ✅ Ожидалось: {location['expected']}")
        print()

def explain_status_logic():
    """Объяснение логики статуса"""
    print("\n🧮 ЛОГИКА ОПРЕДЕЛЕНИЯ СТАТУСА:")
    print("=" * 50)
    
    print("1️⃣ ПОЛУЧЕНИЕ КООРДИНАТ:")
    print("   • Автомобиль отправляет широту и долготу")
    print("   • Данные поступают через OwnTracks → /api/location")
    print()
    
    print("2️⃣ РАСЧЕТ РАССТОЯНИЯ:")
    print("   • Используется формула гаверсинуса")
    print("   • Точность расчета: ±1-2 метра")
    print("   • Учитывается кривизна Земли")
    print()
    
    print("3️⃣ ОПРЕДЕЛЕНИЕ СТАТУСА:")
    print("   • Расстояние ≤ 100м → 🟢 ВОДИТЕЛЬ ОЖИДАЕТ")
    print("   • Расстояние > 100м → 🟡 В ПУТИ")
    print()
    
    print("4️⃣ СОХРАНЕНИЕ В БАЗУ:")
    print("   • Координаты, расстояние и статус записываются")
    print("   • Время записи фиксируется")
    print("   • Данные доступны через API трекера")

def show_work_zone_details():
    """Показать детали рабочей зоны"""
    print("\n🗺️ ДЕТАЛИ РАБОЧЕЙ ЗОНЫ:")
    print("=" * 50)
    
    print(f"📍 ЦЕНТР ЗОНЫ:")
    print(f"   Широта:  55.676803")
    print(f"   Долгота: 37.523510")
    print()
    
    print(f"📏 РАДИУС ЗОНЫ:")
    print(f"   100 метров (настраивается)")
    print()
    
    print(f"🎯 ПЛОЩАДЬ ЗОНЫ:")
    area = math.pi * 100 * 100  # π * r²
    print(f"   {area:,.0f} м² ≈ {area/10000:.1f} гектара")
    print()
    
    print(f"📐 ДИАМЕТР ЗОНЫ:")
    print(f"   200 метров (от края до края)")
    print()
    
    print(f"🚶‍♂️ ВРЕМЯ ПЕШКОМ:")
    print(f"   ~2-3 минуты пешком от края до центра")

def main():
    """Основная демонстрация"""
    demo_status_examples()
    explain_status_logic()
    show_work_zone_details()
    
    print("\n💡 ВАЖНЫЕ МОМЕНТЫ:")
    print("=" * 50)
    print("• Статус обновляется при каждом получении координат")
    print("• GPS точность влияет на определение статуса")
    print("• Рекомендуется настроить OwnTracks на высокую точность")
    print("• Радиус 100м учитывает погрешность GPS (±3-5м)")
    print()
    
    print("🔧 НАСТРОЙКА ЗОНЫ:")
    print("• Координаты центра можно изменить в настройках")
    print("• Радиус можно настроить (по умолчанию 100м)")
    print("• Рекомендуемый радиус: 50-200м в зависимости от объекта")

if __name__ == "__main__":
    main() 