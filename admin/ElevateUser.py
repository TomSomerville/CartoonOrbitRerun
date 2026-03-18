#!/usr/bin/env python
"""Elevate a user account to admin by username."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db
from app.models import User

def elevate():
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("Enter username to elevate: ").strip()

    if not target:
        print("No username provided. Aborted.")
        sys.exit(1)

    try:
        db.connect()

        user = User.get_or_none(User.username ** target)  # ** = ILIKE (case-insensitive)

        if user is None:
            print(f"No user found with username '{target}'.")
            sys.exit(1)

        if user.is_admin:
            print(f"'{user.username}' is already an admin.")
            sys.exit(0)

        user.is_admin = True
        user.save()
        db.close()

        print(f"'{user.username}' has been elevated to admin.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    elevate()
