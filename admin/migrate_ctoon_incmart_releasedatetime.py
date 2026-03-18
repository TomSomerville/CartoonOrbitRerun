#!/usr/bin/env python
"""Migration: add in_cmart column and update release_date to DATETIME."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db

def run():
    db.connect()
    steps = [
        ("in_cmart",     "ALTER TABLE ctoons ADD COLUMN in_cmart BOOLEAN NOT NULL DEFAULT FALSE;"),
        ("release_date", "ALTER TABLE ctoons MODIFY COLUMN release_date DATETIME NULL;"),
    ]
    for label, sql in steps:
        try:
            db.execute_sql(sql)
            print(f"  + {label}")
        except Exception as e:
            print(f"  ~ {label} skipped ({e})")
    db.close()
    print("Migration complete.")

if __name__ == '__main__':
    run()
