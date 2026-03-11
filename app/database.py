import peewee as pw
from config import config

# Database connection
db = pw.MySQLDatabase(
    config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=config.DB_PORT
)

class BaseModel(pw.Model):
    """Base model for all database models"""
    class Meta:
        database = db

# Import all models
from app.models import *
