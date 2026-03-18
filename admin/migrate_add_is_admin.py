#!/usr/bin/env python
"""Migration: add is_admin column to users table (default FALSE)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db

def run():
    try:
        db.connect()
        db.execute_sql(
            "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;"
        )
        db.close()
        print("Migration complete: is_admin column added to users.")
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    run()
