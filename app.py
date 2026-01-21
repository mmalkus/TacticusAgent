from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PLAYER_CACHE_FILE = os.path.join(DATA_DIR, 'player.json')
GUILD_CACHE_FILE = os.path.join(DATA_DIR, 'guild.json')

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

    return render_template('player.html', player=data, updated_at=updated_at)


@app.route('/guild')
def guild():
    """Display guild data."""
    if not get_api_key():
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error, updated_at = fetch_guild_data()
    if error:
        flash(f'Error fetching guild data: {error}', 'error')
        return render_template('guild.html', guild=None, error=error, updated_at=updated_at)

    return render_template('guild.html', guild=data, updated_at=updated_at)


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
