#!/usr/bin/env python
"""Restore the ctoons table from admin/ctoon_seed_data.json.

Safe to run multiple times — skips any cToon whose (name, edition) already
exists in the database so it won't create duplicates on a partial restore.

Typical workflow after a DB wipe:
    1. python init_db.py          — recreate tables
    2. python admin/seed_ctoons.py — restore cToons

Usage:
    python admin/seed_ctoons.py [--dry-run]

Options:
    --dry-run   Print what would be inserted without writing anything.
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db
from app.models import CToon

# ── Paths ─────────────────────────────────────────────────────────────────────

SEED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ctoon_seed_data.json')

# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(val):
    if not val:
        return None
    for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None

# ── Seed ──────────────────────────────────────────────────────────────────────

def seed(dry_run=False):
    if not os.path.isfile(SEED_FILE):
        print(f'ERROR: seed data not found at {SEED_FILE}')
        print('Run admin/export_ctoons.py first to generate it.')
        sys.exit(1)

    with open(SEED_FILE, encoding='utf-8') as f:
        records = json.load(f)

    if not records:
        print('Seed file is empty — nothing to do.')
        return

    db.connect(reuse_if_open=True)

    created = 0
    skipped = 0

    for r in records:
        name    = r.get('name', '')
        edition = r.get('edition', 1)

        # Dedup key: same name + edition already in DB → skip
        exists = CToon.get_or_none(
            (CToon.name == name) & (CToon.edition == edition)
        )
        if exists:
            print(f'  SKIP  {name!r} (edition {edition}) — already exists (id={exists.id})')
            skipped += 1
            continue

        if dry_run:
            print(f'  DRY   {name!r} (edition {edition}, rarity={r.get("rarity")})')
            created += 1
            continue

        CToon.create(
            name         = name,
            description  = r.get('description'),
            image_url    = r.get('image_url', ''),
            rarity       = r.get('rarity', 'common'),
            created_at   = _parse_dt(r.get('created_at')) or datetime.now(),
            mint_count   = r.get('mint_count', 0),
            ctoon_set    = r.get('ctoon_set'),
            series       = r.get('series'),
            release_date = _parse_dt(r.get('release_date')),
            cmart_value  = r.get('cmart_value', 0),
            edition      = edition,
            deletable    = r.get('deletable', False),
            minted       = r.get('minted', 0),
            in_cmart     = r.get('in_cmart', False),
        )
        print(f'  + {name!r} (edition {edition}, rarity={r.get("rarity")})')
        created += 1

    db.close()

    label = 'Would insert' if dry_run else 'Inserted'
    print(f'\nDone. {label} {created} cToon(s), skipped {skipped} duplicate(s).')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Seed cToons table from JSON export.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be inserted without writing to DB.')
    args = parser.parse_args()
    seed(dry_run=args.dry_run)
