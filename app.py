from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os
import json
import re
import statistics
from datetime import datetime
from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PLAYER_CACHE_FILE = os.path.join(DATA_DIR, 'player.json')
GUILD_CACHE_FILE = os.path.join(DATA_DIR, 'guild.json')
GUILD_RAID_CACHE_FILE = os.path.join(DATA_DIR, 'guild_raid.json')
USERNAMES_FILE = os.path.join(DATA_DIR, 'usernames.json')

load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

TACTICUS_API_BASE = 'https://api.tacticusgame.com/api/v1'


@app.template_filter('camel_to_spaces')
def camel_to_spaces(value):
    """Convert camelCase to spaces: ThousandSons -> Thousand Sons"""
    if not value:
        return value
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', value)


@app.template_filter('camel_to_underscores')
def camel_to_underscores(value):
    """Convert camelCase to underscores for wiki links: ThousandSons -> Thousand_Sons"""
    if not value:
        return value
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', value)


@app.template_filter('rank_name')
def rank_name(value):
    """Convert rank number to name: 0 -> Stone I, 9 -> Silver I, etc."""
    if value is None or not isinstance(value, int):
        return value

    tiers = ['Stone', 'Iron', 'Bronze', 'Silver', 'Gold', 'Diamond', 'Adamantine']
    numerals = ['I', 'II', 'III']

    # Ranks are 0-indexed, each tier has 3 levels
    tier_index = value // 3
    level_index = value % 3

    if tier_index < len(tiers):
        return f"{tiers[tier_index]} {numerals[level_index]}"
    else:
        # For ranks beyond defined tiers
        return f"Rank {value}"


@app.template_filter('progression_name')
def progression_name(value):
    """Convert progression index to (rarity, star_count, color_class) based on Tacticus progression."""
    if value is None or not isinstance(value, int):
        return (str(value), 0, 'gold')

    # Progression mapping based on https://tacticus.wiki.gg/wiki/Unit_Progression
    # Known examples from user:
    # - Index 8 (Plagueburst Crawler) = Rare 1 red
    # - Index 13 (Farsight) = Legendary 3 red
    # - Index 15 (Trajann) = Legendary 1 blue
    # - Index 16 (Xybia) = Mythic 1 blue
    # - Index 18 (Neurothrope) = Mythic 3 blue
    # (rarity, star_count, color_class)
    progression_map = {
        1: ('Common', 1, 'gold'),
        2: ('Common', 2, 'gold'),
        3: ('Uncommon', 2, 'gold'),
        4: ('Uncommon', 3, 'gold'),
        5: ('Uncommon', 4, 'gold'),
        6: ('Rare', 4, 'gold'),
        7: ('Rare', 5, 'gold'),
        8: ('Rare', 1, 'red'),
        9: ('Epic', 1, 'red'),         # Plagueburst Crawler
        10: ('Epic', 2, 'red'),
        11: ('Epic', 3, 'red'),
        12: ('Legendary', 3, 'red'),
        13: ('Legendary', 4, 'red'),
        14: ('Legendary', 5, 'red'), 
        15: ('Legendary', 1, 'blue'),  # Trajann
        16: ('Mythic', 1, 'blue'),     # Xybia
        17: ('Mythic', 2, 'blue'),
        18: ('Mythic', 3, 'blue'),     # Neurothrope
        19: ('Mythic', 1, 'wings'),
    }

    if value in progression_map:
        return progression_map[value]
    elif value > 19:
        # Extended wings
        return ('Mythic', value - 18, 'wings')
    else:
        return (f'P{value}', 0, 'gold')


@app.template_filter('progression_stars')
def progression_stars(value):
    """Get the star display for progression."""
    rarity, count, color = progression_name(value)
    if color == 'wings':
        return f"{rarity} Wings" if count == 1 else f"{rarity} Wings {count}"
    return f"{rarity} {'★' * count}"


@app.template_filter('progression_class')
def progression_class(value):
    """Get the color class for progression."""
    _, _, color = progression_name(value)
    return color


def ensure_data_dir():
    """Ensure the data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def save_cached_data(filepath, data):
    """Save data to cache file with timestamp."""
    ensure_data_dir()
    cache = {
        'updated_at': datetime.now().isoformat(),
        'data': data
    }
    with open(filepath, 'w') as f:
        json.dump(cache, f, indent=2)


def load_cached_data(filepath):
    """Load data from cache file."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            cache = json.load(f)
            return cache.get('data'), cache.get('updated_at')
    return None, None


def load_usernames():
    """Load usernames mapping from file."""
    ensure_data_dir()
    if os.path.exists(USERNAMES_FILE):
        with open(USERNAMES_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_username(user_id, username):
    """Save a username for a user ID."""
    usernames = load_usernames()
    usernames[user_id] = username
    with open(USERNAMES_FILE, 'w') as f:
        json.dump(usernames, f, indent=2)


def save_api_key(api_key):
    """Save API key to .env file."""
    set_key(ENV_FILE, 'TACTICUS_API_KEY', api_key)
    os.environ['TACTICUS_API_KEY'] = api_key


def remove_api_key():
    """Remove API key from .env file."""
    if os.path.exists(ENV_FILE):
        # Read current contents, filter out the API key line
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()
        with open(ENV_FILE, 'w') as f:
            for line in lines:
                if not line.startswith('TACTICUS_API_KEY='):
                    f.write(line)
    os.environ.pop('TACTICUS_API_KEY', None)


def get_api_key():
    """Get API key from session or environment."""
    return session.get('api_key') or os.environ.get('TACTICUS_API_KEY')


def get_api_headers():
    """Get headers with API key from session or environment."""
    api_key = get_api_key()
    if not api_key:
        return None
    return {'X-API-KEY': api_key}


def fetch_player_data(use_cache=True):
    """Fetch player data from cache or Tacticus API."""
    if use_cache:
        data, updated_at = load_cached_data(PLAYER_CACHE_FILE)
        if data:
            return data, None, updated_at

    headers = get_api_headers()
    if not headers:
        return None, 'No API key set', None

    try:
        response = requests.get(f'{TACTICUS_API_BASE}/player', headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            save_cached_data(PLAYER_CACHE_FILE, data)
            _, updated_at = load_cached_data(PLAYER_CACHE_FILE)
            return data, None, updated_at
        elif response.status_code == 403:
            return None, 'Invalid API key or insufficient permissions', None
        elif response.status_code == 404:
            return None, 'Player not found', None
        else:
            return None, f'API error: {response.status_code}', None
    except requests.RequestException as e:
        return None, f'Connection error: {str(e)}', None


def fetch_guild_data(use_cache=True):
    """Fetch guild data from cache or Tacticus API."""
    if use_cache:
        data, updated_at = load_cached_data(GUILD_CACHE_FILE)
        if data:
            return data, None, updated_at

    headers = get_api_headers()
    if not headers:
        return None, 'No API key set', None

    try:
        response = requests.get(f'{TACTICUS_API_BASE}/guild', headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            save_cached_data(GUILD_CACHE_FILE, data)
            _, updated_at = load_cached_data(GUILD_CACHE_FILE)
            return data, None, updated_at
        elif response.status_code == 403:
            return None, 'Invalid API key or insufficient permissions (Guild scope required)', None
        elif response.status_code == 404:
            return None, 'Player is not in a guild', None
        else:
            return None, f'API error: {response.status_code}', None
    except requests.RequestException as e:
        return None, f'Connection error: {str(e)}', None


def fetch_guild_raid_data(use_cache=True):
    """Fetch guild raid data from cache or Tacticus API."""
    if use_cache:
        data, updated_at = load_cached_data(GUILD_RAID_CACHE_FILE)
        if data:
            return data, None, updated_at

    headers = get_api_headers()
    if not headers:
        return None, 'No API key set', None

    try:
        response = requests.get(f'{TACTICUS_API_BASE}/guildRaid', headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            save_cached_data(GUILD_RAID_CACHE_FILE, data)
            _, updated_at = load_cached_data(GUILD_RAID_CACHE_FILE)
            return data, None, updated_at
        elif response.status_code == 403:
            return None, 'Invalid API key or insufficient permissions (Guild Raid scope required)', None
        elif response.status_code == 404:
            return None, 'No active guild raid', None
        else:
            return None, f'API error: {response.status_code}', None
    except requests.RequestException as e:
        return None, f'Connection error: {str(e)}', None


@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page - enter API key."""
    # Load API key from .env into session if available
    if not session.get('api_key') and os.environ.get('TACTICUS_API_KEY'):
        session['api_key'] = os.environ.get('TACTICUS_API_KEY')

    if request.method == 'POST':
        api_key = request.form.get('api_key', '').strip()
        if api_key:
            session['api_key'] = api_key
            # Test the API key by fetching player data (skip cache to validate)
            data, error, _ = fetch_player_data(use_cache=False)
            if data:
                save_api_key(api_key)
                flash('Successfully connected to Tacticus API!', 'success')
                return redirect(url_for('player'))
            else:
                session.pop('api_key', None)
                flash(f'Failed to connect: {error}', 'error')
        else:
            flash('Please enter an API key', 'error')

    return render_template('index.html', connected=bool(get_api_key()))


@app.route('/player')
def player():
    """Display player data."""
    if not get_api_key():
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error, updated_at = fetch_player_data()
    if error:
        flash(f'Error fetching player data: {error}', 'error')
        return redirect(url_for('index'))

    # Also fetch guild data for display
    guild_data, _, _ = fetch_guild_data()
    guild_raid_data, _, _ = fetch_guild_raid_data()

    return render_template('player.html', player=data, guild=guild_data, guild_raid=guild_raid_data, updated_at=updated_at)


@app.route('/guild')
def guild():
    """Display guild data."""
    if not get_api_key():
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error, updated_at = fetch_guild_data()
    if error:
        flash(f'Error fetching guild data: {error}', 'error')
        return render_template('guild.html', guild=None, usernames={}, error=error, updated_at=updated_at)

    usernames = load_usernames()
    return render_template('guild.html', guild=data, usernames=usernames, updated_at=updated_at)


@app.route('/api/username', methods=['POST'])
def api_save_username():
    """API endpoint to save a username for a user ID."""
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username', '')

    if not user_id:
        return {'error': 'user_id is required'}, 400

    save_username(user_id, username)
    return {'success': True, 'user_id': user_id, 'username': username}


@app.route('/guild-raid')
def guild_raid():
    """Display guild raid data."""
    if not get_api_key():
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error, updated_at = fetch_guild_raid_data()
    if error:
        flash(f'Error fetching guild raid data: {error}', 'error')
        return render_template('guild_raid.html', raid=None, bosses=[], error=error, updated_at=updated_at)

    # Aggregate damage by boss type + rarity + set
    boss_data = {}
    entries = data.get('entries', [])
    for entry in entries:
        boss_type = entry.get('type', 'Unknown')
        rarity = entry.get('rarity', 'Unknown')
        boss_set = entry.get('set', 0)
        tier = entry.get('tier', 0)
        damage = entry.get('damageDealt', 0)
        damage_type = entry.get('damageType', '')

        key = (boss_type, rarity, boss_set)

        if key in boss_data:
            boss_data[key]['damage'] += damage
            boss_data[key]['tiers'].add(tier)
            if damage_type != 'Bomb':
                boss_data[key]['damage_values'].append(damage)
        else:
            boss_data[key] = {
                'name': boss_type,
                'damage': damage,
                'rarity': rarity,
                'set': boss_set,
                'tiers': {tier},
                'damage_values': [damage] if damage_type != 'Bomb' else []
            }

    # Calculate tier count, average, stddev, min and max
    for boss in boss_data.values():
        boss['tier_count'] = len(boss['tiers'])
        del boss['tiers']

        values = boss['damage_values']
        if len(values) >= 1:
            boss['avg_damage'] = statistics.mean(values)
            boss['stddev'] = statistics.stdev(values) if len(values) >= 2 else 0
            boss['min_damage'] = min(values)
            boss['max_damage'] = max(values)
        else:
            boss['avg_damage'] = 0
            boss['stddev'] = 0
            boss['min_damage'] = 0
            boss['max_damage'] = 0
        del boss['damage_values']

    # Convert to sorted list (by rarity descending, then set descending, then damage descending)
    rarity_order = {'Common': 0, 'Uncommon': 1, 'Rare': 2, 'Epic': 3, 'Legendary': 4, 'Mythic': 5}
    bosses = list(boss_data.values())
    bosses.sort(key=lambda x: (-rarity_order.get(x['rarity'], 99), -x['set'], -x['damage']))

    return render_template('guild_raid.html', raid=data, bosses=bosses, updated_at=updated_at)


@app.route('/guild-raid/boss/<boss_type>/<rarity>/<int:boss_set>')
def guild_raid_boss(boss_type, rarity, boss_set):
    """Display per-player stats for a specific boss."""
    if not get_api_key():
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error, updated_at = fetch_guild_raid_data()
    if error:
        flash(f'Error fetching guild raid data: {error}', 'error')
        return redirect(url_for('guild_raid'))

    # Filter entries for this specific boss
    entries = data.get('entries', [])
    boss_entries = [e for e in entries if
                    e.get('type') == boss_type and
                    e.get('rarity') == rarity and
                    e.get('set') == boss_set]

    # Aggregate per player (excluding bomb damage for stats)
    player_data = {}
    for entry in boss_entries:
        user_id = entry.get('userId', 'Unknown')
        damage = entry.get('damageDealt', 0)
        damage_type = entry.get('damageType', '')

        if user_id not in player_data:
            player_data[user_id] = {
                'user_id': user_id,
                'total_damage': 0,
                'damage_values': [],
                'attack_count': 0
            }

        player_data[user_id]['total_damage'] += damage
        if damage_type != 'Bomb':
            player_data[user_id]['damage_values'].append(damage)
            player_data[user_id]['attack_count'] += 1

    # Calculate stats per player
    usernames = load_usernames()
    players = []
    for user_id, pdata in player_data.items():
        values = pdata['damage_values']
        player = {
            'user_id': user_id,
            'username': usernames.get(user_id, ''),
            'total_damage': pdata['total_damage'],
            'attack_count': pdata['attack_count'],
            'avg_damage': statistics.mean(values) if values else 0,
            'min_damage': min(values) if values else 0,
            'max_damage': max(values) if values else 0
        }
        players.append(player)

    # Sort by total damage descending
    players.sort(key=lambda x: -x['total_damage'])

    boss_info = {
        'name': boss_type,
        'rarity': rarity,
        'set': boss_set
    }

    return render_template('guild_raid_boss.html', boss=boss_info, players=players, updated_at=updated_at)


@app.route('/characters')
def characters():
    """Display character list."""
    if not get_api_key():
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error, updated_at = fetch_player_data()
    if error:
        flash(f'Error fetching player data: {error}', 'error')
        return redirect(url_for('index'))

    # Get units from nested structure: data.player.units
    player_data = data.get('player', {})
    units = player_data.get('units', [])

    # Sort units by rank (highest first) then by xpLevel
    units_sorted = sorted(units, key=lambda u: (-u.get('rank', 0), -u.get('xpLevel', 0)))

    return render_template('characters.html', units=units_sorted, updated_at=updated_at)


@app.route('/update')
def update():
    """Refresh data from API."""
    if not get_api_key():
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    # Fetch fresh data from API
    data, error, _ = fetch_player_data(use_cache=False)
    if error:
        flash(f'Error updating player data: {error}', 'error')
    else:
        flash('Player data updated successfully!', 'success')

    # Also try to update guild data
    guild_data, guild_error, _ = fetch_guild_data(use_cache=False)
    if guild_data:
        flash('Guild data updated successfully!', 'success')

    # Also try to update guild raid data
    guild_raid_data, guild_raid_error, _ = fetch_guild_raid_data(use_cache=False)
    if guild_raid_data:
        flash('Guild raid data updated successfully!', 'success')

    # Redirect back to the referring page or player page
    return redirect(request.referrer or url_for('player'))


@app.route('/disconnect')
def disconnect():
    """Clear API key and disconnect."""
    session.pop('api_key', None)
    remove_api_key()
    flash('Disconnected from Tacticus API', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
