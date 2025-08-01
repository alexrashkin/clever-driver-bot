# Simple Python classes to replace Django models
from datetime import datetime

class TrackingStatus:
    """Simple tracking status class"""
    def __init__(self, id=1, is_tracking=False):
        self.id = id
        self.is_tracking = is_tracking
        self.last_updated = datetime.now()
    
    @classmethod
    def objects(cls):
        """Mock objects manager"""
        return cls
    
    @classmethod 
    def get_or_create(cls, **kwargs):
        """Mock get_or_create method"""
        # This is a simple mock - in real usage this would interact with database
        instance = cls(**kwargs)
        created = True
        return instance, created
        
    def save(self):
        """Mock save method"""
        self.last_updated = datetime.now()

class Location:
    """Simple location class"""
    def __init__(self, latitude=0, longitude=0, distance=None, is_at_work=False):
        self.latitude = latitude
        self.longitude = longitude  
        self.distance = distance
        self.is_at_work = is_at_work
        self.timestamp = datetime.now()
    
    @classmethod
    def objects(cls):
        """Mock objects manager"""
        return cls
        
    @classmethod
    def create(cls, **kwargs):
        """Mock create method"""
        # This is a simple mock - in real usage this would save to database
        instance = cls(**kwargs)
        return instance

    def __str__(self):
        return f"Координаты: {self.latitude}, {self.longitude} ({self.timestamp})" 