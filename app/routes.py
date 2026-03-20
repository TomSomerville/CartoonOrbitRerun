import secrets
import requests
import os
from collections import Counter
from urllib.parse import urlencode
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, abort, jsonify
from werkzeug.utils import secure_filename
from app.models import User, UserCToon, CToon, CZoneItem, CZone
from app.database import db
import peewee as pw
import random

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _slugify(text):
    """Lowercase, strip special chars, spaces → underscores."""
    import re
    if not text:
        return 'uncategorized'
    text = text.lower()
    text = re.sub(r"['\"]", '', text)        # drop apostrophes / quotes
    text = re.sub(r'[^\w\s]', '_', text)     # other non-word chars → _
    text = re.sub(r'[\s_]+', '_', text)      # collapse spaces / underscores
    return text.strip('_') or 'uncategorized'

main_bp = Blueprint('main', __name__)


@main_bp.route('/sw.js')
def service_worker():
    response = current_app.send_static_file('sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@main_bp.app_context_processor
def inject_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return {'current_user': None, 'unique_ctoons': 0, 'total_ctoons': 0, 'reset_timestamp': _next_reset_ms()}

    user = User.get_or_none(User.id == user_id)
    if not user:
        return {'current_user': None, 'unique_ctoons': 0, 'total_ctoons': 0, 'reset_timestamp': _next_reset_ms()}

    total_ctoons = UserCToon.select().where(UserCToon.user == user).count()
    unique_ctoons = (
        UserCToon.select(pw.fn.COUNT(UserCToon.ctoon_id.distinct()))
        .where(UserCToon.user == user)
        .scalar() or 0
    )

    return {
        'current_user': user,
        'unique_ctoons': unique_ctoons,
        'total_ctoons': total_ctoons,
        'reset_timestamp': _next_reset_ms(),
    }


def _next_reset_ms():
    """Unix timestamp (ms) of the next 8 PM server time."""
    now = datetime.now()
    reset = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if now >= reset:
        reset += timedelta(days=1)
    return int(reset.timestamp()) * 1000


@main_bp.route('/')
@main_bp.route('/index')
def index():
    return render_template('index.html', title='Index')


def _discord_avatar_url(user):
    if user.avatar:
        ext = 'gif' if user.avatar.startswith('a_') else 'png'
        return f'https://cdn.discordapp.com/avatars/{user.discord_id}/{user.avatar}.{ext}?size=64'
    default_idx = (int(user.discord_id) >> 22) % 6
    return f'https://cdn.discordapp.com/embed/avatars/{default_idx}.png'


def _get_or_create_czone(user):
    czone = CZone.get_or_none(CZone.user == user)
    if not czone:
        czone = CZone.create(user=user, background_url=_get_czone_default_bg())
    return czone


@main_bp.route('/czone')
def czone_home():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your cZone.', 'info')
        return redirect(url_for('main.index'))
    return redirect(url_for('main.czone_view', user_id=user_id))


@main_bp.route('/czone/<int:user_id>')
def czone_view(user_id):
    current_user_id = session.get('user_id')
    current = User.get_or_none(User.id == current_user_id) if current_user_id else None

    owner = User.get_or_none(User.id == user_id)
    if not owner:
        abort(404)

    czone = _get_or_create_czone(owner)
    items = list(
        CZoneItem.select(CZoneItem, CToon)
        .join(CToon)
        .where(CZoneItem.czone == czone)
        .order_by(CZoneItem.z_index)
    )

    is_own = bool(current and current.id == owner.id)

    owned_ctoons = []
    ctoon_mint_map = {}  # ctoon_id → first mint_number the owner has
    if is_own:
        all_owned = list(
            UserCToon.select(UserCToon, CToon)
            .join(CToon)
            .where(UserCToon.user == current)
            .order_by(CToon.name, UserCToon.mint_number)
        )

        # Build mint map from full collection (includes placed copies)
        for uc in all_owned:
            cid = uc.ctoon_id
            if cid not in ctoon_mint_map:
                ctoon_mint_map[cid] = uc.mint_number

        # Count how many of each ctoon are already placed in this czone
        placed_counts = Counter(item.ctoon_id for item in items)

        # Exclude that many copies from the widget list (lowest mint numbers first)
        seen = Counter()
        for uc in all_owned:
            cid = uc.ctoon_id
            if seen[cid] < placed_counts[cid]:
                seen[cid] += 1  # this copy is already placed — skip it
                continue
            owned_ctoons.append(uc)

    bg_dir = _czone_bg_dir()
    try:
        czone_backgrounds = sorted(f for f in os.listdir(bg_dir) if _allowed_file(f))
    except OSError:
        czone_backgrounds = []

    default_bg = _get_czone_default_bg()
    user_bg = czone.background_url  # filename or None
    if user_bg:
        canvas_bg_url = f'/czone-bg/{user_bg}'
    elif default_bg:
        canvas_bg_url = f'/czone-bg/{default_bg}'
    else:
        canvas_bg_url = None

    return render_template(
        'czone.html',
        title=f"{owner.username or owner.discord_username}'s cZone",
        czone=czone,
        czone_owner=owner,
        czone_items=items,
        is_own=is_own,
        owned_ctoons=owned_ctoons,
        ctoon_mint_map=ctoon_mint_map,
        avatar_url=_discord_avatar_url(owner),
        canvas_bg_url=canvas_bg_url,
        czone_backgrounds=czone_backgrounds,
        current_bg=user_bg,
    )


@main_bp.route('/czone/nav/first')
def czone_nav_first():
    owner = User.select().join(CZone).order_by(User.id).first()
    if owner:
        return redirect(url_for('main.czone_view', user_id=owner.id))
    return redirect(url_for('main.czone_home'))


@main_bp.route('/czone/nav/last')
def czone_nav_last():
    owner = User.select().join(CZone).order_by(User.id.desc()).first()
    if owner:
        return redirect(url_for('main.czone_view', user_id=owner.id))
    return redirect(url_for('main.czone_home'))


@main_bp.route('/czone/nav/prev/<int:user_id>')
def czone_nav_prev(user_id):
    prev_owner = (User.select().join(CZone)
                  .where(User.id < user_id)
                  .order_by(User.id.desc())
                  .first())
    if not prev_owner:
        prev_owner = User.select().join(CZone).order_by(User.id.desc()).first()
    if prev_owner:
        return redirect(url_for('main.czone_view', user_id=prev_owner.id))
    return redirect(url_for('main.czone_home'))


@main_bp.route('/czone/nav/next/<int:user_id>')
def czone_nav_next(user_id):
    next_owner = (User.select().join(CZone)
                  .where(User.id > user_id)
                  .order_by(User.id)
                  .first())
    if not next_owner:
        next_owner = User.select().join(CZone).order_by(User.id).first()
    if next_owner:
        return redirect(url_for('main.czone_view', user_id=next_owner.id))
    return redirect(url_for('main.czone_home'))


@main_bp.route('/czone/nav/random')
def czone_nav_random():
    users = list(User.select().join(CZone))
    if users:
        return redirect(url_for('main.czone_view', user_id=random.choice(users).id))
    return redirect(url_for('main.czone_home'))


@main_bp.route('/czone/place', methods=['POST'])
def czone_place():
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user:
        return jsonify({'error': 'not_logged_in'}), 401

    data = request.get_json() or {}
    ctoon_id = data.get('ctoon_id')
    x = int(data.get('x', 0))
    y = int(data.get('y', 0))

    ctoon = CToon.get_or_none(CToon.id == ctoon_id)
    if not ctoon:
        return jsonify({'error': 'not_found'}), 404
    if not UserCToon.select().where((UserCToon.user == user) & (UserCToon.ctoon == ctoon)).exists():
        return jsonify({'error': 'not_owned'}), 403

    czone = _get_or_create_czone(user)
    max_z = CZoneItem.select(pw.fn.MAX(CZoneItem.z_index)).where(CZoneItem.czone == czone).scalar() or 0
    item = CZoneItem.create(czone=czone, ctoon=ctoon, position_x=x, position_y=y, z_index=max_z + 1)

    return jsonify({'success': True, 'item_id': item.id, 'z_index': item.z_index})


@main_bp.route('/czone/move/<int:item_id>', methods=['POST'])
def czone_move(item_id):
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user:
        return jsonify({'error': 'not_logged_in'}), 401

    item = CZoneItem.get_or_none(CZoneItem.id == item_id)
    if not item:
        return jsonify({'error': 'not_found'}), 404
    czone_obj = CZone.get_or_none((CZone.id == item.czone_id) & (CZone.user == user))
    if not czone_obj:
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json() or {}
    item.position_x = int(data.get('x', item.position_x))
    item.position_y = int(data.get('y', item.position_y))
    max_z = CZoneItem.select(pw.fn.MAX(CZoneItem.z_index)).where(CZoneItem.czone == czone_obj).scalar() or 0
    item.z_index = max_z + 1
    item.save()

    return jsonify({'success': True, 'z_index': item.z_index})


@main_bp.route('/czone/remove/<int:item_id>', methods=['POST'])
def czone_remove(item_id):
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user:
        return jsonify({'error': 'not_logged_in'}), 401

    item = CZoneItem.get_or_none(CZoneItem.id == item_id)
    if not item:
        return jsonify({'error': 'not_found'}), 404
    czone_obj = CZone.get_or_none((CZone.id == item.czone_id) & (CZone.user == user))
    if not czone_obj:
        return jsonify({'error': 'forbidden'}), 403

    item.delete_instance()
    return jsonify({'success': True})


@main_bp.route('/czone/save', methods=['POST'])
def czone_save():
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user:
        return jsonify({'error': 'not_logged_in'}), 401

    czone = _get_or_create_czone(user)
    data = request.get_json() or {}
    items = data.get('items', [])

    for entry in items:
        item_id = entry.get('item_id')
        if not item_id:
            continue
        item = CZoneItem.get_or_none(
            (CZoneItem.id == item_id) & (CZoneItem.czone == czone)
        )
        if item:
            item.position_x = int(entry.get('x', item.position_x))
            item.position_y = int(entry.get('y', item.position_y))
            item.save()

    return jsonify({'success': True})


@main_bp.route('/czone/clear', methods=['POST'])
def czone_clear():
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user:
        return jsonify({'error': 'not_logged_in'}), 401

    czone = _get_or_create_czone(user)
    CZoneItem.delete().where(CZoneItem.czone == czone).execute()
    return jsonify({'success': True})


@main_bp.route('/cmart')
def cmart():
    ctoons = list(CToon.select().where(CToon.in_cmart == True).order_by(CToon.name))
    new_cutoff = datetime.now() - timedelta(days=7)
    return render_template('cmart.html', title='cMart', ctoons=ctoons, new_cutoff=new_cutoff)


@main_bp.route('/cmart/buy/<int:ctoon_id>', methods=['POST'])
def cmart_buy(ctoon_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'not_logged_in', 'message': 'You must be logged in to buy.'}), 401

    user = User.get_or_none(User.id == user_id)
    if not user:
        return jsonify({'error': 'not_logged_in', 'message': 'You must be logged in to buy.'}), 401

    ctoon = CToon.get_or_none(CToon.id == ctoon_id)
    if not ctoon or not ctoon.in_cmart:
        return jsonify({'error': 'not_available', 'message': 'This cToon is not available in the cMart.'}), 400

    if user.points < ctoon.cmart_value:
        return jsonify({'error': 'insufficient_points', 'message': f'Not enough points. Need {ctoon.cmart_value}, have {user.points}.'}), 400

    with db.atomic():
        # Atomically claim the next mint number
        if ctoon.mint_count > 0:
            updated = (CToon.update(minted=CToon.minted + 1)
                       .where((CToon.id == ctoon_id) & (CToon.minted < CToon.mint_count))
                       .execute())
        else:
            updated = (CToon.update(minted=CToon.minted + 1)
                       .where(CToon.id == ctoon_id)
                       .execute())

        if not updated:
            return jsonify({'error': 'sold_out', 'message': 'This cToon just sold out!'}), 400

        ctoon = CToon.get_by_id(ctoon_id)
        mint_number = ctoon.minted

        User.update(points=User.points - ctoon.cmart_value).where(User.id == user_id).execute()

        UserCToon.create(
            user=user,
            ctoon=ctoon,
            mint_number=mint_number,
            acquired_via='cmart',
        )

    user = User.get_by_id(user_id)
    sold_out = ctoon.mint_count > 0 and mint_number >= ctoon.mint_count
    return jsonify({
        'success': True,
        'mint_number': mint_number,
        'mint_count': ctoon.mint_count,
        'new_points': user.points,
        'sold_out': sold_out,
        'ctoon_name': ctoon.name,
    }), 200


@main_bp.route('/collection')
def collection():
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user:
        flash('Please log in to view your collection.', 'info')
        return redirect(url_for('main.index'))

    user_ctoons = (UserCToon.select(UserCToon, CToon)
                   .join(CToon)
                   .where(UserCToon.user == user)
                   .order_by(CToon.name, UserCToon.mint_number))

    return render_template('collection.html', title='My Collection', user_ctoons=list(user_ctoons))


@main_bp.route('/auth/discord')
def discord_login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    params = urlencode({
        'client_id': current_app.config['DISCORD_CLIENT_ID'],
        'redirect_uri': current_app.config['DISCORD_REDIRECT_URI'],
        'response_type': 'code',
        'scope': 'identify',
        'state': state,
    })
    return redirect(f'https://discord.com/oauth2/authorize?{params}')


@main_bp.route('/auth/discord/callback')
def discord_callback():
    error = request.args.get('error')
    if error:
        flash('Discord login was cancelled.', 'danger')
        return redirect(url_for('main.index'))

    state = request.args.get('state')
    if not state or state != session.pop('oauth_state', None):
        flash('Invalid OAuth state. Please try again.', 'danger')
        return redirect(url_for('main.index'))

    code = request.args.get('code')
    token_resp = requests.post(
        'https://discord.com/api/oauth2/token',
        data={
            'client_id': current_app.config['DISCORD_CLIENT_ID'],
            'client_secret': current_app.config['DISCORD_CLIENT_SECRET'],
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': current_app.config['DISCORD_REDIRECT_URI'],
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    if not token_resp.ok:
        flash('Failed to authenticate with Discord. Please try again.', 'danger')
        return redirect(url_for('main.index'))

    access_token = token_resp.json()['access_token']

    user_resp = requests.get(
        'https://discord.com/api/users/@me',
        headers={'Authorization': f'Bearer {access_token}'},
    )

    if not user_resp.ok:
        flash('Failed to fetch your Discord profile. Please try again.', 'danger')
        return redirect(url_for('main.index'))

    discord_data = user_resp.json()
    discord_id = discord_data['id']
    discord_username = discord_data.get('global_name') or discord_data['username']
    avatar = discord_data.get('avatar')

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip:
        ip = ip.split(',')[0].strip()

    user = User.get_or_none(User.discord_id == discord_id)

    if user:
        if not user.is_active:
            flash('Your account has been disabled.', 'danger')
            return redirect(url_for('main.index'))
        user.discord_username = discord_username
        user.avatar = avatar
        user.last_login = datetime.now()
        user.last_ip = ip
        user.save()
    else:
        user = User.create(
            discord_id=discord_id,
            discord_username=discord_username,
            avatar=avatar,
            last_login=datetime.now(),
            last_ip=ip,
        )

    session['user_id'] = user.id
    return redirect(url_for('main.index'))


@main_bp.route('/auth/setup-username', methods=['POST'])
def setup_username():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.index'))

    user = User.get_or_none(User.id == user_id)
    if not user or user.username:
        return redirect(url_for('main.index'))

    username = request.form.get('username', '').strip()
    if not username:
        flash('Username is required.', 'danger')
    elif len(username) < 3 or len(username) > 50:
        flash('Username must be between 3 and 50 characters.', 'danger')
    elif not all(c.isalnum() or c in ('_', '-') for c in username):
        flash('Username may only contain letters, numbers, underscores, and hyphens.', 'danger')
    elif User.get_or_none(User.username == username):
        flash('That username is already taken.', 'danger')
    else:
        user.username = username
        user.save()
        flash(f'Welcome to Cartoon Orbit Rerun, {username}!', 'success')

    return redirect(url_for('main.index'))


@main_bp.route('/admin')
def administration():
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user or not user.is_admin:
        abort(403)

    now = datetime.now()
    week_ago = now - timedelta(days=7)

    bg_dir = _czone_bg_dir()
    try:
        czone_backgrounds = sorted(
            f for f in os.listdir(bg_dir)
            if _allowed_file(f)
        )
    except OSError:
        czone_backgrounds = []

    stats = {
        'total_users': User.select().count(),
        'active_today': User.select().where(User.last_login >= now.replace(hour=0, minute=0, second=0, microsecond=0)).count(),
        'new_this_week': User.select().where(User.created_at >= week_ago).count(),
        'recent_users': list(User.select().order_by(User.created_at.desc()).limit(10)),
        'all_users': list(User.select().order_by(User.created_at.desc())),
        'all_ctoons': list(CToon.select().order_by(CToon.name)),
        'ctoon_sets': sorted(set(
            c.ctoon_set for c in CToon.select(CToon.ctoon_set).distinct() if c.ctoon_set
        )),
        'ctoon_series': sorted(set(
            c.series for c in CToon.select(CToon.series).distinct() if c.series
        )),
        'czone_backgrounds': czone_backgrounds,
        'czone_default_bg': _get_czone_default_bg(),
        'globals': _get_globals(),
    }

    return render_template('administration.html', title='Administration', stats=stats,
                           globals=stats['globals'])


def _get_admin():
    user_id = session.get('user_id')
    admin = User.get_or_none(User.id == user_id) if user_id else None
    if not admin or not admin.is_admin:
        abort(403)
    return admin


def _czone_bg_dir():
    configured = current_app.config.get('CTOON_UPLOAD_DIR', '').strip()
    base = configured if configured else os.path.join(current_app.static_folder, 'ctoons')
    path = os.path.join(base, 'czone_backgrounds')
    os.makedirs(path, exist_ok=True)
    return path


def _get_czone_default_bg():
    """Return the default background filename, or None if not set."""
    default_file = os.path.join(_czone_bg_dir(), '_default.txt')
    if os.path.isfile(default_file):
        try:
            with open(default_file, 'r') as f:
                return f.read().strip() or None
        except OSError:
            pass
    return None


_RARITY_KEYS = [
    'common', 'uncommon', 'rare', 'very rare',
    'crazy rare', 'prize only', 'code only', 'auction only',
]

_GLOBALS_DEFAULTS = {
    'common':       {'mint_count': 500,  'cmart_value': 100},
    'uncommon':     {'mint_count': 400,  'cmart_value': 200},
    'rare':         {'mint_count': 300,  'cmart_value': 400},
    'very rare':    {'mint_count': 200,  'cmart_value': 750},
    'crazy rare':   {'mint_count': 100,  'cmart_value': 1250},
    'prize only':   {'mint_count': -1,   'cmart_value': 200},
    'code only':    {'mint_count': -1,   'cmart_value': 200},
    'auction only': {'mint_count': 100,  'cmart_value': 1250},
}


def _globals_file():
    return os.path.join(os.path.dirname(current_app.root_path), 'globals.json')


def _get_globals():
    import json
    try:
        with open(_globals_file(), 'r') as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    # Ensure every rarity key exists with a full set of defaults
    result = {}
    for key in _RARITY_KEYS:
        defaults = _GLOBALS_DEFAULTS.get(key, {'mint_count': 0, 'cmart_value': 0})
        saved    = data.get(key, {})
        result[key] = {
            'mint_count':  int(saved.get('mint_count',  defaults['mint_count'])),
            'cmart_value': int(saved.get('cmart_value', defaults['cmart_value'])),
        }
    return result


def _admin_redirect():
    tab = request.form.get('active_tab', '')
    url = url_for('main.administration')
    if tab:
        url += '?tab=' + tab
    return redirect(url)


@main_bp.route('/admin/disable-users', methods=['POST'])
def admin_disable_users():
    admin = _get_admin()
    selected_ids = request.form.getlist('user_ids')
    if selected_ids:
        User.update(is_active=False).where(
            (User.id << selected_ids) & (User.id != admin.id)
        ).execute()
    return _admin_redirect()


@main_bp.route('/admin/enable-users', methods=['POST'])
def admin_enable_users():
    _get_admin()
    selected_ids = request.form.getlist('user_ids')
    if selected_ids:
        User.update(is_active=True).where(User.id << selected_ids).execute()
    return _admin_redirect()


@main_bp.route('/admin/ctoon/mark-deletable', methods=['POST'])
def admin_ctoon_mark_deletable():
    _get_admin()
    selected_ids = request.form.getlist('ctoon_ids')
    if selected_ids:
        CToon.update(deletable=True).where(CToon.id << selected_ids).execute()
    return _admin_redirect()


@main_bp.route('/admin/ctoon/unmark-deletable', methods=['POST'])
def admin_ctoon_unmark_deletable():
    _get_admin()
    selected_ids = request.form.getlist('ctoon_ids')
    if selected_ids:
        CToon.update(deletable=False).where(CToon.id << selected_ids).execute()
    return _admin_redirect()


@main_bp.route('/admin/ctoon/delete-marked', methods=['POST'])
def admin_ctoon_delete_marked():
    _get_admin()
    marked = list(CToon.select().where(CToon.deletable == True))
    if marked:
        ids = [c.id for c in marked]
        CZoneItem.delete().where(CZoneItem.ctoon << ids).execute()
        UserCToon.delete().where(UserCToon.ctoon << ids).execute()
        CToon.delete().where(CToon.id << ids).execute()
    return _admin_redirect()


@main_bp.route('/admin/ctoon/upload', methods=['POST'])
def admin_ctoon_upload():
    _get_admin()

    configured = current_app.config.get('CTOON_UPLOAD_DIR', '').strip()
    base_dir = configured if configured else os.path.join(current_app.static_folder, 'ctoons')

    files       = request.files.getlist('images')
    names       = request.form.getlist('name')
    sets        = request.form.getlist('ctoon_set')
    series_list = request.form.getlist('series')
    rarities    = request.form.getlist('rarity')
    editions    = request.form.getlist('edition')
    mint_counts = request.form.getlist('mint_count')
    cmart_vals  = request.form.getlist('cmart_value')
    rel_dates   = request.form.getlist('release_date')
    descs       = request.form.getlist('description')

    def _get(lst, idx, default=''):
        return lst[idx].strip() if idx < len(lst) else default

    for i, f in enumerate(files):
        if not f or not _allowed_file(f.filename):
            continue

        series_val  = _get(series_list, i)
        set_val     = _get(sets, i)
        series_slug = _slugify(series_val)
        set_slug    = _slugify(set_val)

        # Build nested save directory: base / series / set
        save_dir = os.path.join(base_dir, series_slug, set_slug)
        os.makedirs(save_dir, exist_ok=True)

        # Lowercase filename, no collision suffix needed (path is unique per series/set)
        original = secure_filename(f.filename)
        filename = original.lower()
        save_path = os.path.join(save_dir, filename)
        f.save(save_path)

        # Derive URL: relative to static_folder if possible, else serve via /ctoon-img/
        static_folder = os.path.abspath(current_app.static_folder)
        abs_save = os.path.abspath(save_path)
        if abs_save.startswith(static_folder):
            rel = os.path.relpath(abs_save, static_folder).replace('\\', '/')
            image_url = f'/static/{rel}'
        else:
            rel = os.path.relpath(abs_save, base_dir).replace('\\', '/')
            image_url = f'/ctoon-img/{rel}'

        raw_date = _get(rel_dates, i)
        if raw_date:
            try:
                release_date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                release_date = datetime.now()
        else:
            release_date = datetime.now()

        base_name = os.path.splitext(original)[0]
        CToon.create(
            name         = _get(names, i) or base_name,
            ctoon_set    = set_val or None,
            series       = series_val or None,
            rarity       = _get(rarities, i, 'common'),
            edition      = int(_get(editions, i, '1') or 1),
            mint_count   = int(_get(mint_counts, i, '0') or 0),
            cmart_value  = int(_get(cmart_vals, i, '0') or 0),
            release_date = release_date,
            description  = _get(descs, i) or None,
            image_url    = image_url,
            minted       = 0,
            in_cmart     = False,
        )

    return _admin_redirect()


@main_bp.route('/admin/ctoon/<int:ctoon_id>/edit', methods=['POST'])
def admin_ctoon_edit(ctoon_id):
    _get_admin()
    ctoon = CToon.get_or_none(CToon.id == ctoon_id)
    if not ctoon:
        abort(404)

    ctoon.name         = request.form.get('name', ctoon.name).strip()
    ctoon.ctoon_set    = request.form.get('ctoon_set', '').strip() or None
    ctoon.series       = request.form.get('series', '').strip() or None
    ctoon.rarity       = request.form.get('rarity', ctoon.rarity).strip()
    ctoon.edition      = int(request.form.get('edition') or ctoon.edition)
    ctoon.mint_count   = int(request.form.get('mint_count') or ctoon.mint_count)
    ctoon.cmart_value  = int(request.form.get('cmart_value') or ctoon.cmart_value)
    raw_date = request.form.get('release_date', '').strip()
    if raw_date:
        try:
            ctoon.release_date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    else:
        ctoon.release_date = None
    ctoon.in_cmart = 'in_cmart' in request.form
    ctoon.description  = request.form.get('description', '').strip() or None
    ctoon.image_url    = request.form.get('image_url', ctoon.image_url).strip()
    ctoon.save()

    return _admin_redirect()



@main_bp.route('/ctoon-img/<path:filepath>')
def ctoon_image(filepath):
    configured = current_app.config.get('CTOON_UPLOAD_DIR', '').strip()
    base_dir = configured if configured else os.path.join(current_app.static_folder, 'ctoons')
    from flask import send_from_directory
    return send_from_directory(base_dir, filepath)


@main_bp.route('/czone-bg/<path:filename>')
def czone_bg_image(filename):
    from flask import send_from_directory
    return send_from_directory(_czone_bg_dir(), filename)


@main_bp.route('/admin/czone-bg/upload', methods=['POST'])
def admin_czone_bg_upload():
    _get_admin()
    bg_dir = _czone_bg_dir()
    for f in request.files.getlist('backgrounds'):
        if f and _allowed_file(f.filename):
            filename = secure_filename(f.filename).lower()
            f.save(os.path.join(bg_dir, filename))
    return _admin_redirect()


@main_bp.route('/admin/czone-bg/set-default', methods=['POST'])
def admin_czone_bg_set_default():
    _get_admin()
    data = request.get_json() or {}
    filename = secure_filename(data.get('filename', '').strip())
    default_file = os.path.join(_czone_bg_dir(), '_default.txt')
    if filename:
        if not os.path.isfile(os.path.join(_czone_bg_dir(), filename)):
            return jsonify({'error': 'not_found'}), 404
        with open(default_file, 'w') as f:
            f.write(filename)
    else:
        if os.path.isfile(default_file):
            os.remove(default_file)
    return jsonify({'success': True})


@main_bp.route('/admin/globals/save', methods=['POST'])
def admin_globals_save():
    import json
    _get_admin()
    data = request.get_json() or {}
    current = _get_globals()
    for key in _RARITY_KEYS:
        if key in data:
            entry = data[key]
            current[key] = {
                'mint_count':  max(-1, int(entry.get('mint_count',  current[key]['mint_count']))),
                'cmart_value': max(0, int(entry.get('cmart_value', current[key]['cmart_value']))),
            }
    with open(_globals_file(), 'w') as f:
        json.dump(current, f, indent=2)
    return jsonify({'success': True})


@main_bp.route('/czone/set-background', methods=['POST'])
def czone_set_background():
    user_id = session.get('user_id')
    user = User.get_or_none(User.id == user_id) if user_id else None
    if not user:
        return jsonify({'error': 'not_logged_in'}), 401

    data = request.get_json() or {}
    filename = data.get('filename') or None

    czone = _get_or_create_czone(user)
    if filename:
        safe = secure_filename(filename)
        if not os.path.isfile(os.path.join(_czone_bg_dir(), safe)):
            return jsonify({'error': 'not_found'}), 404
        czone.background_url = safe
    else:
        czone.background_url = None
    czone.save()

    default_bg = _get_czone_default_bg()
    active = czone.background_url or default_bg
    bg_url = f'/czone-bg/{active}' if active else None
    return jsonify({'success': True, 'bg_url': bg_url})


@main_bp.route('/admin/czone-bg/delete', methods=['POST'])
def admin_czone_bg_delete():
    _get_admin()
    filename = secure_filename(request.form.get('filename', ''))
    if filename:
        path = os.path.join(_czone_bg_dir(), filename)
        if os.path.isfile(path):
            os.remove(path)
    return _admin_redirect()


@main_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
