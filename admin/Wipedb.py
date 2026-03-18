#!/usr/bin/env python
"""Wipe all data from all database tables (preserves table structure)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db
from app.models import User, CToon, UserCToon, CZone, CZoneItem, Buddy, Auction

TABLES = [Auction, Buddy, CZoneItem, CZone, UserCToon, CToon, User]

def wipe_db():
    confirmation = input(
        "\n⚠️  WARNING: This will permanently delete ALL data in the database.\n"
        "Type 'yes' to confirm: "
    ).strip()

    if confirmation.lower() != 'yes':
        print("Aborted.")
        sys.exit(0)

    try:
        db.connect()
        print("Connected to database.")

        with db.atomic():
            for table in TABLES:
                count = table.delete().execute()
                print(f"  Cleared {table.__name__}: {count} rows deleted.")

        db.close()
        print("\nDatabase wiped successfully.")

    except Exception as e:
        print(f"\nError wiping database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    wipe_db()
