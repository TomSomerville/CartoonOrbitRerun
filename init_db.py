#!/usr/bin/env python
"""Initialize the database and create tables"""
import sys
from app.database import db
from app.models import User, CToon, UserCToon, CZone, CZoneItem

TABLES = [User, CToon, UserCToon, CZone, CZoneItem]

def init_db():
    """Drop and recreate all tables"""
    try:
        db.connect()
        print("Connected to database successfully!")

        db.execute_sql('SET FOREIGN_KEY_CHECKS=0;')
        db.drop_tables(TABLES, safe=True, cascade=False)
        db.execute_sql('SET FOREIGN_KEY_CHECKS=1;')
        print("Old tables dropped.")

        db.create_tables(TABLES, safe=True)
        print("Database tables created successfully!")

        db.close()
        print("Database initialization complete!")
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    init_db()
