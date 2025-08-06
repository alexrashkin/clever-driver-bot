import React, { useState, useEffect, useRef } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Alert,
  PermissionsAndroid,
  Platform,
} from 'react-native';
import Geolocation from 'react-native-geolocation-service';
import BackgroundTimer from 'react-native-background-timer';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = 'https://cleverdriver.ru/api/location';

const App = () => {
  const [isTracking, setIsTracking] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [lastSent, setLastSent] = useState(null);
  const [sentCount, setSentCount] = useState(0);
  const [errorCount, setErrorCount] = useState(0);
  const [uptime, setUptime] = useState(0);
  const [interval, setInterval] = useState(30); // секунды
  const [nextUpdate, setNextUpdate] = useState(0);
  
  const trackingRef = useRef(null);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    // Загружаем сохраненные настройки
    loadSettings();
    
    // Запрашиваем разрешения при запуске
    requestPermissions();
    
    return () => {
      if (trackingRef.current) {
        Geolocation.clearWatch(trackingRef.current);
      }
      if (timerRef.current) {
        BackgroundTimer.clearInterval(timerRef.current);
      }
    };
  }, []);

  const loadSettings = async () => {
    try {
      const savedInterval = await AsyncStorage.getItem('tracking_interval');
      if (savedInterval) {
        setInterval(parseInt(savedInterval));
      }
      
      const savedSentCount = await AsyncStorage.getItem('sent_count');
      if (savedSentCount) {
        setSentCount(parseInt(savedSentCount));
      }
      
      const savedErrorCount = await AsyncStorage.getItem('error_count');
      if (savedErrorCount) {
        setErrorCount(parseInt(savedErrorCount));
      }
    } catch (error) {
      console.log('Ошибка загрузки настроек:', error);
    }
  };

  const saveSettings = async () => {
    try {
      await AsyncStorage.setItem('tracking_interval', interval.toString());
      await AsyncStorage.setItem('sent_count', sentCount.toString());
      await AsyncStorage.setItem('error_count', errorCount.toString());
    } catch (error) {
      console.log('Ошибка сохранения настроек:', error);
    }
  };

  const requestPermissions = async () => {
    if (Platform.OS === 'ios') {
      Geolocation.requestAuthorization('always');
    } else {
      try {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          {
            title: 'Разрешение на геолокацию',
            message: 'Приложению нужен доступ к геолокации для отслеживания',
            buttonNeutral: 'Спросить позже',
            buttonNegative: 'Отмена',
            buttonPositive: 'OK',
          },
        );
        if (granted === PermissionsAndroid.RESULTS.GRANTED) {
          console.log('Разрешение на геолокацию получено');
        } else {
          Alert.alert('Ошибка', 'Необходимо разрешение на геолокацию');
        }
      } catch (err) {
        console.warn(err);
      }
    }
  };

  const startTracking = () => {
    if (isTracking) return;

    setIsTracking(true);
    startTimeRef.current = Date.now();
    
    // Начинаем отслеживание геолокации
    trackingRef.current = Geolocation.watchPosition(
      (position) => {
        setCurrentLocation(position);
        console.log('Новые координаты:', position.coords);
      },
      (error) => {
        console.log('Ошибка геолокации:', error);
        setErrorCount(prev => prev + 1);
      },
      {
        enableHighAccuracy: true,
        distanceFilter: 10, // метры
        interval: 10000, // 10 секунд
        fastestInterval: 5000, // 5 секунд
      }
    );

    // Запускаем таймер для отправки координат
    timerRef.current = BackgroundTimer.setInterval(() => {
      if (currentLocation) {
        sendLocation();
      }
    }, interval * 1000);

    // Запускаем таймер для обновления UI
    const uiTimer = setInterval(() => {
      if (startTimeRef.current) {
        const uptimeSeconds = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setUptime(uptimeSeconds);
        
        // Вычисляем время до следующей отправки
        const timeSinceLastSend = uptimeSeconds % interval;
        setNextUpdate(interval - timeSinceLastSend);
      }
    }, 1000);

    console.log('Отслеживание запущено');
  };

  const stopTracking = () => {
    if (!isTracking) return;

    setIsTracking(false);
    
    if (trackingRef.current) {
      Geolocation.clearWatch(trackingRef.current);
      trackingRef.current = null;
    }
    
    if (timerRef.current) {
      BackgroundTimer.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    startTimeRef.current = null;
    setUptime(0);
    setNextUpdate(0);
    
    console.log('Отслеживание остановлено');
  };

  const sendLocation = async () => {
    if (!currentLocation) return;

    const data = {
      _type: 'location',
      lat: currentLocation.coords.latitude,
      lon: currentLocation.coords.longitude,
      tst: Math.floor(Date.now() / 1000),
      accuracy: currentLocation.coords.accuracy,
      altitude: currentLocation.coords.altitude || null,
      speed: currentLocation.coords.speed || null,
      heading: currentLocation.coords.heading || null,
    };

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        setSentCount(prev => prev + 1);
        setLastSent(new Date().toLocaleTimeString());
        console.log('Координаты отправлены:', data);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      setErrorCount(prev => prev + 1);
      console.log('Ошибка отправки:', error);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatCoordinates = (coords) => {
    if (!coords) return 'Нет данных';
    return `${coords.latitude.toFixed(6)}, ${coords.longitude.toFixed(6)}`;
  };

  // Сохраняем настройки при изменении
  useEffect(() => {
    saveSettings();
  }, [sentCount, errorCount, interval]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f8f9fa" />
      
      <ScrollView contentInsetAdjustmentBehavior="automatic" style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.title}>🚗 Умный водитель</Text>
          <Text style={styles.subtitle}>Простой трекер</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>⚙️ Настройки</Text>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Интервал отправки:</Text>
            <Text style={styles.settingValue}>{interval} сек</Text>
          </View>
          <TouchableOpacity
            style={[styles.button, isTracking ? styles.buttonStop : styles.buttonStart]}
            onPress={isTracking ? stopTracking : startTracking}
          >
            <Text style={styles.buttonText}>
              {isTracking ? '⏹️ Остановить' : '▶️ Начать отслеживание'}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>📍 Текущие координаты</Text>
          <Text style={styles.coordinates}>
            {formatCoordinates(currentLocation?.coords)}
          </Text>
          {currentLocation && (
            <View style={styles.locationDetails}>
              <Text style={styles.detailText}>
                Точность: {Math.round(currentLocation.coords.accuracy)}м
              </Text>
              <Text style={styles.detailText}>
                Следующая отправка: {nextUpdate}с
              </Text>
            </View>
          )}
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>📊 Статистика</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Отправлено</Text>
              <Text style={styles.statValue}>{sentCount}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Ошибок</Text>
              <Text style={styles.statValue}>{errorCount}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Время работы</Text>
              <Text style={styles.statValue}>{formatTime(uptime)}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Последняя отправка</Text>
              <Text style={styles.statValue}>{lastSent || '--'}</Text>
            </View>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>ℹ️ Информация</Text>
          <Text style={styles.infoText}>
            • Приложение отправляет координаты каждые {interval} секунд
          </Text>
          <Text style={styles.infoText}>
            • Работает в фоновом режиме
          </Text>
          <Text style={styles.infoText}>
            • Использует высокую точность GPS
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    backgroundColor: '#667eea',
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  card: {
    backgroundColor: 'white',
    margin: 15,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2d3748',
    marginBottom: 15,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  settingLabel: {
    fontSize: 16,
    color: '#4a5568',
  },
  settingValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3748',
  },
  button: {
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonStart: {
    backgroundColor: '#48bb78',
  },
  buttonStop: {
    backgroundColor: '#e53e3e',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  coordinates: {
    fontSize: 14,
    fontFamily: 'monospace',
    color: '#2d3748',
    backgroundColor: '#f7fafc',
    padding: 10,
    borderRadius: 6,
    marginBottom: 10,
  },
  locationDetails: {
    marginTop: 10,
  },
  detailText: {
    fontSize: 14,
    color: '#4a5568',
    marginBottom: 5,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    width: '48%',
    backgroundColor: '#f7fafc',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#718096',
    marginBottom: 5,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2d3748',
  },
  infoText: {
    fontSize: 14,
    color: '#4a5568',
    marginBottom: 8,
    lineHeight: 20,
  },
});

export default App; 