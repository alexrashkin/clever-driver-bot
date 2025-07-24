# Simple Python classes to replace Django models for API compatibility

class TrackingStatus:
    """Simple tracking status class"""
    def __init__(self, is_active=False):
        self.is_active = is_active
    
    @classmethod
    def objects(cls):
        """Mock objects manager"""
        return cls
    
    @classmethod 
    def get_or_create(cls, **kwargs):
        """Mock get_or_create method"""
        # This is a simple mock - in real usage this would interact with database
        instance = cls()
        created = True
        return instance, created

class Location:
    """Simple location class"""
    def __init__(self, latitude=0, longitude=0, distance=None, is_at_work=False):
        self.latitude = latitude
        self.longitude = longitude  
        self.distance = distance
        self.is_at_work = is_at_work
        self.timestamp = None
    
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

__all__ = ['TrackingStatus', 'Location'] 