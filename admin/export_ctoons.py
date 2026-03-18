#!/usr/bin/env python
"""Export all cToons from the database to admin/ctoon_seed_data.json.

Run this once to capture the current DB state. The output file is read by
seed_ctoons.py to restore the ctoons table after a wipe.

Image URL remapping:
  /static/ctoons/...  → /static/seedtoons/...  (already copied)
  /ctoon-img/...      → /static/seedtoons/...  (copies file from CTOON_UPLOAD_DIR)

Usage:
    python admin/export_ctoons.py
"""
import sys
import os
import json
import shutil
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import db
from app.models import CToon
from config import config

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR   = os.path.join(BASE_DIR, 'app', 'static')
SEEDTOONS_DIR = os.path.join(STATIC_DIR, 'seedtoons')
OUTPUT_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ctoon_seed_data.json')

CTOON_UPLOAD_DIR = config.CTOON_UPLOAD_DIR or os.path.join(STATIC_DIR, 'ctoons')

# ── URL remapping ──────────────────────────────────────────────────────────────

def _remap_image_url(image_url: str) -> str:
    """
    Remap image_url to point at /static/seedtoons/. Also copies the file
    into seedtoons if it lives in an external CTOON_UPLOAD_DIR (/ctoon-img/).
    Returns the remapped URL, or the original if it can't be resolved.
    """
    if not image_url:
        return image_url

    # /static/ctoons/... → /static/seedtoons/...
    if image_url.startswith('/static/ctoons/'):
        rel = image_url[len('/static/ctoons/'):]
        return f'/static/seedtoons/{rel}'

    # /ctoon-img/...  → copy from CTOON_UPLOAD_DIR then remap
    if image_url.startswith('/ctoon-img/'):
        rel = image_url[len('/ctoon-img/'):]
        src = os.path.join(CTOON_UPLOAD_DIR, rel)
        dst = os.path.join(SEEDTOONS_DIR, rel)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f'  Copied external image: {rel}')
        else:
            print(f'  WARNING: external image not found: {src}')
        return f'/static/seedtoons/{rel}'

    # Already points at seedtoons or some other URL — leave unchanged
    return image_url


def _ctoon_to_dict(c: CToon) -> dict:
    return {
        'name':         c.name,
        'description':  c.description,
        'image_url':    _remap_image_url(c.image_url),
        'rarity':       c.rarity,
        'created_at':   c.created_at.isoformat() if c.created_at else None,
        'mint_count':   c.mint_count,
        'ctoon_set':    c.ctoon_set,
        'series':       c.series,
        'release_date': c.release_date.isoformat() if c.release_date else None,
        'cmart_value':  c.cmart_value,
        'edition':      c.edition,
        'deletable':    c.deletable,
        'minted':       c.minted,
        'in_cmart':     c.in_cmart,
    }


def export():
    os.makedirs(SEEDTOONS_DIR, exist_ok=True)
    db.connect(reuse_if_open=True)

    ctoons = list(CToon.select().order_by(CToon.id))
    if not ctoons:
        print('No cToons found in database. Nothing to export.')
        db.close()
        return

    data = [_ctoon_to_dict(c) for c in ctoons]
    db.close()

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'Exported {len(data)} cToon(s) -> {OUTPUT_FILE}')
    print('Run seed_ctoons.py to restore after a DB wipe.')


if __name__ == '__main__':
    export()
