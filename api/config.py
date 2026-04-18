"""
Configuration settings for the Irrigation Network Recommendation System API
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # API settings
    API_TITLE = "Sistema de Recomendación para Diseño de Redes de Riego"
    API_VERSION = "1.0.0"
    
    # Google Elevation API
    GOOGLE_ELEVATION_API_KEY = os.getenv('GOOGLE_ELEVATION_API_KEY', '')
    GOOGLE_ELEVATION_API_URL = 'https://maps.googleapis.com/maps/api/elevation/json'
    
    # Default parameters for hydraulic calculations
    DEFAULT_WATER_DENSITY = 1000  # kg/m³
    DEFAULT_GRAVITY = 9.81  # m/s²
    DEFAULT_HAZEN_WILLIAMS_C = 150  # For HDPE tubing
    
    # Drip emitter parameters
    DEFAULT_EMITTER_EXPONENT_MIN = 0.5  # Non-compensated drippers
    DEFAULT_EMITTER_EXPONENT_MAX = 0.6  # Non-compensated drippers
    
    # Pressure conversions
    PRESSURE_BAR_PER_METER = 0.098  # bar/m of water column
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max file size
    ALLOWED_EXTENSIONS = {'tif', 'tiff', 'geotiff', 'png', 'jpg', 'jpeg'}
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    GOOGLE_ELEVATION_API_KEY = 'test_key'
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Add security settings for production


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
