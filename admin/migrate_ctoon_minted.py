#!/usr/bin/env python
"""Migration: add minted column to ctoons table."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db

def run():
    try:
        db.connect()
        db.execute_sql("ALTER TABLE ctoons ADD COLUMN minted INT NOT NULL DEFAULT 0;")
        db.close()
        print("Migration complete: minted column added to ctoons.")
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    run()
