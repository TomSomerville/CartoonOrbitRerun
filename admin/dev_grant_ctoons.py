#!/usr/bin/env python
"""Dev tool: grant 2 cMart ctoons to every active user and place them in their cZone.

Picks ctoons at random from the available (non-sold-out) cMart stock. Minting
follows the same atomic pattern as the real cMart buy route so mint numbers
are correct. Each ctoon is placed at a random location in the user's cZone.

Safe to run multiple times — it will keep granting and placing on every run,
so only use this for fresh test databases.

Usage:
    python admin/dev_grant_ctoons.py
    python admin/dev_grant_ctoons.py --dry-run
    python admin/dev_grant_ctoons.py --count 3   # grant 3 ctoons per user (default 2)
"""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db
from app.models import User, CToon, UserCToon, CZone, CZoneItem
import peewee as pw

# ── Canvas bounds used for random placement ────────────────────────────────────
# Conservative estimate: canvas is roughly 560 x 400 px; items are 80x80.
CANVAS_W  = 480
CANVAS_H  = 320
ITEM_SIZE = 80


# ── Helpers ───────────────────────────────────────────────────────────────────

def _available_ctoons():
    """Return all in-cmart ctoons that still have stock (or are unlimited)."""
    results = []
    for c in CToon.select().where(CToon.in_cmart == True).order_by(CToon.name):
        if c.mint_count > 0 and c.minted >= c.mint_count:
            continue  # sold out
        results.append(c)
    return results


def _get_or_create_czone(user):
    czone = CZone.get_or_none(CZone.user == user)
    if not czone:
        czone = CZone.create(user=user)
    return czone


def _random_pos():
    x = random.randint(0, CANVAS_W - ITEM_SIZE)
    y = random.randint(0, CANVAS_H - ITEM_SIZE)
    return x, y


def _grant_and_place(user, ctoon, czone, dry_run):
    """
    Atomically mint one copy of ctoon for user, then place it in their cZone.
    Returns (mint_number, x, y) on success, or None if the ctoon sold out mid-run.
    """
    if dry_run:
        # Read the would-be mint number without committing
        fake_mint = ctoon.minted + 1
        x, y = _random_pos()
        return fake_mint, x, y

    with db.atomic():
        if ctoon.mint_count > 0:
            updated = (CToon.update(minted=CToon.minted + 1)
                       .where((CToon.id == ctoon.id) & (CToon.minted < CToon.mint_count))
                       .execute())
        else:
            updated = (CToon.update(minted=CToon.minted + 1)
                       .where(CToon.id == ctoon.id)
                       .execute())

        if not updated:
            return None  # sold out between check and mint

        ctoon = CToon.get_by_id(ctoon.id)
        mint_number = ctoon.minted

        UserCToon.create(
            user=user,
            ctoon=ctoon,
            mint_number=mint_number,
            acquired_via='prize',
        )

    x, y = _random_pos()
    max_z = (CZoneItem.select(pw.fn.MAX(CZoneItem.z_index))
             .where(CZoneItem.czone == czone).scalar() or 0)
    CZoneItem.create(
        czone=czone,
        ctoon=ctoon,
        position_x=x,
        position_y=y,
        z_index=max_z + 1,
    )

    return mint_number, x, y


# ── Main ──────────────────────────────────────────────────────────────────────

def run(count=2, dry_run=False):
    db.connect(reuse_if_open=True)

    available = _available_ctoons()
    if not available:
        print('No available ctoons in cMart. Nothing to do.')
        db.close()
        return

    users = list(User.select().where(User.is_active == True).order_by(User.id))
    if not users:
        print('No active users found.')
        db.close()
        return

    grant_count  = min(count, len(available))
    mode_label   = '[DRY RUN] ' if dry_run else ''
    print(f'{mode_label}Granting {grant_count} ctoon(s) to {len(users)} active user(s) '
          f'({len(available)} available in cMart)\n')

    total_granted = 0
    total_placed  = 0
    total_skipped = 0

    for user in users:
        label = user.username or user.discord_username
        picks = random.sample(available, grant_count)
        czone = _get_or_create_czone(user) if not dry_run else None

        for ctoon in picks:
            result = _grant_and_place(user, ctoon, czone, dry_run)
            if result is None:
                print(f'  SKIP  {label} <- {ctoon.name} (sold out mid-run)')
                total_skipped += 1
                continue

            mint_number, x, y = result
            prefix = 'DRY' if dry_run else '  +'
            print(f'  {prefix}  {label} <- {ctoon.name} #{mint_number}  placed @ ({x}, {y})')
            total_granted += 1
            if not dry_run:
                total_placed += 1

    db.close()
    if dry_run:
        print(f'\nDry run complete. Would grant {total_granted} ctoon(s), '
              f'skip {total_skipped}.')
    else:
        print(f'\nDone. {total_granted} ctoon(s) granted and placed, '
              f'{total_skipped} skipped (sold out).')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Grant cMart ctoons to all active users and place in their cZone.'
    )
    parser.add_argument('--count', type=int, default=2,
                        help='Number of ctoons to grant per user (default: 2)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would happen without writing to the DB.')
    args = parser.parse_args()
    run(count=args.count, dry_run=args.dry_run)
