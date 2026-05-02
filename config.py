import os
from urllib.parse import quote

# Get the absolute path of this config file's directory
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fitness-saas-secret-key-2026'
    
    # Use SQLite for development (change to MySQL for production)
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')
    
    # Database configuration - set all variables regardless of type for config access
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_NAME = os.environ.get('DB_NAME', 'fitness_db')
    
    if DB_TYPE == 'mysql':
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    else:
        # SQLite for local development
        # Use AppData for reliability on Windows with spaces in usernames
        import tempfile
        
        # Try using instance directory first, fallback to temp
        instance_dir = os.path.join(CONFIG_DIR, 'instance')
        try:
            os.makedirs(instance_dir, exist_ok=True)
            # Test if we can write to this directory
            test_file = os.path.join(instance_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            db_file = os.path.join(instance_dir, 'fitness.db')
        except (OSError, IOError):
            # Fallback to temp directory if we can't write to instance
            db_file = os.path.join(tempfile.gettempdir(), 'fitness.db')
            print(f"Warning: Using temp directory for database: {db_file}")
        
        # Ensure forward slashes for SQLite URI
        db_file = db_file.replace('\\', '/')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_file}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    
    # Session configuration
    from datetime import timedelta
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    
    # AI / LLM configuration
    GEMINI_API_KEY = os.environ.get('AIzaSyAQJypkelUr7eaAAVwRk8AWX-SF2cGfN2E', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
