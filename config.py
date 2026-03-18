import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', True)
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'cartoon_orbit')
    DB_PORT = int(os.getenv('DB_PORT', 3306))

    # cToon image storage — absolute path; leave empty to use app/static/ctoons/
    CTOON_UPLOAD_DIR = os.getenv('CTOON_UPLOAD_DIR', '')

    # Discord OAuth
    DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '')
    DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET', '')
    DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/auth/discord/callback')

config = Config()
