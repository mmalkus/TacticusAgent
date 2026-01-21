from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

TACTICUS_API_BASE = 'https://api.tacticusgame.com/api/v1'


def get_api_headers():
    """Get headers with API key from session."""
    api_key = session.get('api_key')
    if not api_key:
        return None
    return {'X-API-KEY': api_key}


def fetch_player_data():
    """Fetch player data from Tacticus API."""
    headers = get_api_headers()
    if not headers:
        return None, 'No API key set'

    try:
        response = requests.get(f'{TACTICUS_API_BASE}/player', headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 403:
            return None, 'Invalid API key or insufficient permissions'
        elif response.status_code == 404:
            return None, 'Player not found'
        else:
            return None, f'API error: {response.status_code}'
    except requests.RequestException as e:
        return None, f'Connection error: {str(e)}'


def fetch_guild_data():
    """Fetch guild data from Tacticus API."""
    headers = get_api_headers()
    if not headers:
        return None, 'No API key set'

    try:
        response = requests.get(f'{TACTICUS_API_BASE}/guild', headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 403:
            return None, 'Invalid API key or insufficient permissions (Guild scope required)'
        elif response.status_code == 404:
            return None, 'Player is not in a guild'
        else:
            return None, f'API error: {response.status_code}'
    except requests.RequestException as e:
        return None, f'Connection error: {str(e)}'


@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page - enter API key."""
    if request.method == 'POST':
        api_key = request.form.get('api_key', '').strip()
        if api_key:
            session['api_key'] = api_key
            # Test the API key by fetching player data
            data, error = fetch_player_data()
            if data:
                flash('Successfully connected to Tacticus API!', 'success')
                return redirect(url_for('player'))
            else:
                session.pop('api_key', None)
                flash(f'Failed to connect: {error}', 'error')
        else:
            flash('Please enter an API key', 'error')

    return render_template('index.html', connected=bool(session.get('api_key')))


@app.route('/player')
def player():
    """Display player data."""
    if not session.get('api_key'):
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error = fetch_player_data()
    if error:
        flash(f'Error fetching player data: {error}', 'error')
        return redirect(url_for('index'))

    return render_template('player.html', player=data)


@app.route('/guild')
def guild():
    """Display guild data."""
    if not session.get('api_key'):
        flash('Please enter your API key first', 'error')
        return redirect(url_for('index'))

    data, error = fetch_guild_data()
    if error:
        flash(f'Error fetching guild data: {error}', 'error')
        return render_template('guild.html', guild=None, error=error)

    return render_template('guild.html', guild=data)


@app.route('/disconnect')
def disconnect():
    """Clear API key and disconnect."""
    session.pop('api_key', None)
    flash('Disconnected from Tacticus API', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
