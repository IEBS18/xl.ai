# config.py
"""
Configuration settings for the Flask CSV Analysis application
"""

import os
from pathlib import Path


class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here-change-in-production')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # CORS settings
    ALLOWED_ORIGINS = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://preview--data-scope-ai-lens.lovable.app",
        "https://*.lovable.app",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ]
    
    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY = os.getenv('AZUREAPI')
    AZURE_OPENAI_VERSION = os.getenv('AZUREVERSION', '2024-02-01')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZUREENDPOINT')
    AZURE_DEPLOYMENT_NAME = os.getenv('AZURE_DEPLOYMENT_NAME', 'gpt-4')
    
    # SocketIO settings
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    SOCKETIO_TRANSPORTS = ['polling', 'websocket']
    
    # Application directories
    BASE_DIR = Path(__file__).parent
    UPLOADS_DIR = BASE_DIR / UPLOAD_FOLDER
    OUTPUTS_DIR = BASE_DIR / 'outputs'
    IMAGES_DIR = OUTPUTS_DIR / 'images'
    REPORTS_DIR = OUTPUTS_DIR / 'reports'
    DATA_DIR = OUTPUTS_DIR / 'data'
    
    # Database settings (for auth)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # Analysis settings
    DEFAULT_MODEL = "gpt-4o-mini"
    CODE_EXECUTION_TIMEOUT = 60  # seconds
    MAX_REGENERATION_ATTEMPTS = 3
    
    # Conversation history settings
    MAX_CONVERSATION_HISTORY = 50
    LANGCHAIN_MAX_TOKEN_LIMIT = 2000
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.UPLOADS_DIR,
            cls.OUTPUTS_DIR,
            cls.IMAGES_DIR,
            cls.REPORTS_DIR,
            cls.DATA_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
    
    @classmethod
    def validate_azure_config(cls):
        """Validate Azure OpenAI configuration"""
        required_vars = [
            ('AZUREAPI', cls.AZURE_OPENAI_API_KEY),
            ('AZUREVERSION', cls.AZURE_OPENAI_VERSION),
            ('AZUREENDPOINT', cls.AZURE_OPENAI_ENDPOINT)
        ]
        
        missing_vars = [name for name, value in required_vars if not value]
        
        if missing_vars:
            print(f"❌ Missing environment variables mazi iccha: {missing_vars}")
            print("Please set the following:")
            print("- AZUREAPI: Your Azure OpenAI API key")
            print("- AZUREVERSION: API version (e.g., '2024-02-01')")
            print("- AZUREENDPOINT: Your Azure OpenAI endpoint")
            return False
        
        return True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    SOCKETIO_LOGGER = True
    SOCKETIO_ENGINEIO_LOGGER = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Secure settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Disable logging in production
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Reduced timeouts for faster tests
    CODE_EXECUTION_TIMEOUT = 30
    SOCKETIO_PING_TIMEOUT = 30


# Configuration mapping
config_mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config_mapping.get(config_name, DevelopmentConfig)