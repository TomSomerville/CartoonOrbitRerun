#!/usr/bin/env python
"""Migration: add new fields to ctoons table."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db

COLUMNS = [
    "ALTER TABLE ctoons ADD COLUMN mint_count INT NOT NULL DEFAULT 0;",
    "ALTER TABLE ctoons ADD COLUMN ctoon_set VARCHAR(100) NULL;",
    "ALTER TABLE ctoons ADD COLUMN series VARCHAR(100) NULL;",
    "ALTER TABLE ctoons ADD COLUMN release_date DATE NULL;",
    "ALTER TABLE ctoons ADD COLUMN cmart_value INT NOT NULL DEFAULT 0;",
    "ALTER TABLE ctoons ADD COLUMN edition INT NOT NULL DEFAULT 1;",
    "ALTER TABLE ctoons ADD COLUMN deletable BOOLEAN NOT NULL DEFAULT FALSE;",
]

def run():
    db.connect()
    for sql in COLUMNS:
        col = sql.split('ADD COLUMN')[1].strip().split()[0]
        try:
            db.execute_sql(sql)
            print(f"  + {col}")
        except Exception as e:
            print(f"  ~ {col} skipped ({e})")
    db.close()
    print("Migration complete.")

if __name__ == '__main__':
    run()
