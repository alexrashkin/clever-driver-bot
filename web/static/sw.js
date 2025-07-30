// Service Worker для фонового отслеживания
const CACHE_NAME = 'driver-tracker-v2';
const SERVER_URL = self.location.origin; // Динамический URL вместо localhost

// Установка Service Worker
self.addEventListener('install', (event) => {
    console.log('Service Worker установлен');
    self.skipWaiting();
});

// Активация Service Worker
self.addEventListener('activate', (event) => {
    console.log('Service Worker активирован');
    event.waitUntil(
        // Очищаем старые кеши при обновлении
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Удаляем старый кеш:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});

// Обработка push-уведомлений
self.addEventListener('push', (event) => {
    console.log('Получено push-уведомление');
    
    const options = {
        body: 'Проверка местоположения',
        icon: '/static/icon.svg',
        badge: '/static/icon.svg',
        data: {
            url: '/mobile_tracker.html'
        },
        requireInteraction: true,
        actions: [
            {
                action: 'open',
                title: 'Открыть',
                icon: '/static/icon.svg'
            },
            {
                action: 'close',
                title: 'Закрыть',
                icon: '/static/icon.svg'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Driver Tracker', options)
    );
});

// Обработка клика по уведомлению
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            self.clients.openWindow('/mobile_tracker.html')
        );
    }
});

// Обработка сообщений от клиента
self.addEventListener('message', (event) => {
    if (event.data.type === 'sendLocation') {
        sendLocationToServer(event.data.location);
    }
});

// Отправка местоположения на сервер
async function sendLocationToServer(location) {
    try {
        const response = await fetch(`${SERVER_URL}/api/location`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                latitude: location.latitude,
                longitude: location.longitude
            })
        });
        
        const data = await response.json();
        if (data.success) {
            console.log('Местоположение отправлено из Service Worker');
            return true;
        } else {
            console.error('Ошибка отправки из Service Worker:', data.error);
            return false;
        }
    } catch (error) {
        console.error('Ошибка Service Worker:', error);
        return false;
    }
}

// Периодическая проверка активности
setInterval(() => {
    self.clients.matchAll().then(clients => {
        if (clients.length > 0) {
            clients.forEach(client => {
                client.postMessage({type: 'ping'});
            });
        }
    });
}, 30000); // Каждые 30 секунд 