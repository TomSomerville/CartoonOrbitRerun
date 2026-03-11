from app.database import BaseModel
import peewee as pw
from datetime import datetime

class User(BaseModel):
    """User model"""
    username = pw.CharField(unique=True)
    email = pw.CharField(unique=True)
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'users'
