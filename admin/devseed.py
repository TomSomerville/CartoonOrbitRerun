#!/usr/bin/env python
"""Seed the database with realistic fake users for development.

Running the script multiple times is safe — it skips users that already exist
and backfills any missing related records (e.g. CZones) for pre-existing users.
"""
import sys
import os
import random
import string
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db
from app.models import User, CZone

# ── Name pools ────────────────────────────────────────────────────────────────

FIRST = [
    'Jake', 'Mia', 'Tyler', 'Chloe', 'Marcus', 'Lily', 'Devon', 'Sara',
    'Nate', 'Zoe', 'Ryan', 'Emma', 'Cole', 'Aiden', 'Jade', 'Logan',
    'Haley', 'Owen', 'Brianna', 'Ethan',
]

LAST = [
    'Smith', 'Chen', 'Rivera', 'Patel', 'Johnson', 'Kim', 'Brown',
    'Martinez', 'Taylor', 'Davis', 'Wilson', 'Moore', 'Anderson', 'Harris',
]

# Cartoon-Network-flavored username fragments
UN_PREFIX = [
    'Cartoon', 'Toon', 'Orbit', 'Rerun', 'Mega', 'Ultra', 'Super',
    'Hyper', 'Cosmic', 'Radical', 'Retro', 'Turbo', 'Neon', 'Pixel',
]
UN_SUFFIX = [
    'Fan', 'Watcher', 'Kid', 'Dude', 'Hero', 'Star', 'Guy', 'Nerd',
    'Geek', 'Buff', 'Ace', 'Pro', 'Runner', 'Chaser',
]

# Common private/ISP IP ranges (fake but realistic-looking)
IP_NETS = [
    '192.168.{}.{}',
    '10.0.{}.{}',
    '172.16.{}.{}',
    '73.{}.{}.{}',
    '98.{}.{}.{}',
    '174.{}.{}.{}',
    '67.{}.{}.{}',
]

CZONE_NAMES = [
    'My cZone',
    'My cZone',          # weighted toward default
    'My cZone',
    'Cartoon Corner',
    'Toon Town',
    'The Zone',
    'My Gallery',
    'Orbit Space',
    'My Hangout',
    'Cool Zone',
    'Toon Zone',
    'The Toon Room',
    'Cartoon Collection',
]

CZONE_DESCS = [
    None,               # Most users leave it blank
    None,
    None,
    None,
    'Welcome to my cZone!',
    'Check out my collection!',
    'My favorite Cartoon Network characters.',
    'Come visit my toons!',
    'Collecting since day one.',
    'Best cZone on Cartoon Orbit!',
    "CN was the best. Change my mind.",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _avatar_hash():
    """Real Discord avatar hashes are 32-char hex strings."""
    return ''.join(random.choices(string.hexdigits[:16], k=32))

def _discord_id():
    """Discord snowflakes are 17–19 digits."""
    return str(random.randint(10**16, 10**18 - 1))

def _discord_username(first, last):
    styles = [
        f'{first.lower()}{last.lower()}{random.randint(1, 9999)}',
        f'{first.lower()}_{last.lower()}',
        f'{last.lower()}{random.randint(10, 99)}',
        f'{first.lower()}.{last.lower()}',
    ]
    return random.choice(styles)

def _username():
    prefix = random.choice(UN_PREFIX)
    suffix = random.choice(UN_SUFFIX)
    num    = random.randint(1, 999)
    styles = [
        f'{prefix}{suffix}',
        f'{prefix}{suffix}{num}',
        f'{prefix}_{suffix}',
        f'{prefix}{num}',
    ]
    return random.choice(styles)

def _ip():
    template = random.choice(IP_NETS)
    return template.format(
        random.randint(1, 254),
        random.randint(1, 254),
        random.randint(1, 254),
    )

def _date_between(start, end):
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta))

def _make_czone(user, joined_at):
    """Create a CZone for a user if they don't already have one."""
    if CZone.get_or_none(CZone.user == user):
        return False

    czone_created = _date_between(joined_at, joined_at + timedelta(days=7))
    CZone.create(
        user         = user,
        name         = random.choice(CZONE_NAMES),
        background_url = None,
        description  = random.choice(CZONE_DESCS),
        is_public    = random.random() > 0.05,   # ~5% private
        created_at   = czone_created,
        updated_at   = czone_created,
    )
    return True

# ── Seed ──────────────────────────────────────────────────────────────────────

def seed(count=10):
    db.connect(reuse_if_open=True)

    now    = datetime.now()
    oldest = now - timedelta(days=365)

    users_created  = 0
    users_skipped  = 0
    czones_created = 0

    # ── Create new users ──────────────────────────────────────────────────────
    for _ in range(count):
        first = random.choice(FIRST)
        last  = random.choice(LAST)

        discord_id       = _discord_id()
        discord_username = _discord_username(first, last)
        username         = _username()
        avatar           = _avatar_hash() if random.random() > 0.15 else None
        points           = random.randint(0, 2500)
        joined_at        = _date_between(oldest, now - timedelta(days=1))
        last_login       = _date_between(joined_at, now) if random.random() > 0.1 else None
        last_ip          = _ip() if last_login else None

        if User.get_or_none(User.discord_id == discord_id):
            users_skipped += 1
            continue
        if User.get_or_none(User.username == username):
            username = username + str(random.randint(10, 99))

        user = User.create(
            discord_id       = discord_id,
            discord_username = discord_username,
            username         = username,
            avatar           = avatar,
            points           = points,
            created_at       = joined_at,
            updated_at       = joined_at,
            last_login       = last_login,
            last_ip          = last_ip,
            is_active        = random.random() > 0.1,
            is_admin         = False,
        )
        users_created += 1

        if _make_czone(user, joined_at):
            czones_created += 1

        print(f'  + {username} ({discord_username})')

    # ── Backfill CZones for any existing users that are missing one ───────────
    backfilled = 0
    for user in User.select():
        if _make_czone(user, user.created_at):
            backfilled += 1
            czones_created += 1

    db.close()
    print(
        f'\nDone. '
        f'{users_created} users created, {users_skipped} skipped (collision). '
        f'{czones_created} cZones created ({backfilled} backfilled for existing users).'
    )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Seed dev database.')
    parser.add_argument('--count', type=int, default=10,
                        help='Number of users to attempt to create (default: 10)')
    args = parser.parse_args()
    seed(args.count)
