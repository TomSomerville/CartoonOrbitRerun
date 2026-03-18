#!/usr/bin/env python
"""Migration: add last_ip column to users table."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db

def run():
    try:
        db.connect()
        db.execute_sql(
            "ALTER TABLE users ADD COLUMN last_ip VARCHAR(45) NULL;"
        )
        db.close()
        print("Migration complete: last_ip column added to users.")
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    run()
