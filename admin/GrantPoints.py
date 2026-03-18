#!/usr/bin/env python
"""Grant points to a user account.

Usage:
    python admin/GrantPoints.py <username> <points>
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db
from app.models import User


def grant_points(username, points):
    db.connect()

    user = User.get_or_none(User.username ** username)
    if user is None:
        print(f"No user found with username '{username}'.")
        sys.exit(1)

    user.points += points
    user.save()
    db.close()

    action = "Granted" if points >= 0 else "Deducted"
    print(f"{action} {abs(points)} points to '{user.username}'. New balance: {user.points}.")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python admin/GrantPoints.py <username> <points>")
        sys.exit(1)

    username = sys.argv[1]

    try:
        points = int(sys.argv[2])
    except ValueError:
        print(f"Error: '{sys.argv[2]}' is not a valid integer.")
        sys.exit(1)

    grant_points(username, points)
