#!/usr/bin/env python
"""Initialize the database and create tables"""
import sys
from app.database import db
from app.models import User

def init_db():
    """Create all tables"""
    try:
        db.connect()
        print("✓ Connected to database successfully!")
        
        # Create tables
        db.create_tables([User], safe=True)
        print("✓ Database tables created successfully!")
        
        db.close()
        print("\n✅ Database initialization complete!")
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    init_db()
