# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TacticusAgent is a Python Flask web application that displays player data from the Warhammer 40,000: Tacticus mobile game using the official Tacticus API.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
python app.py
# Or with Flask CLI
flask run --debug

# The app runs at http://localhost:5000
```

## Architecture

### Application Structure
- `app.py` - Main Flask application with routes and API client logic
- `templates/` - Jinja2 HTML templates
  - `base.html` - Base template with navigation and layout
  - `index.html` - API key entry page
  - `player.html` - Player data display
  - `guild.html` - Guild data display
- `static/style.css` - Dark-themed CSS styling

### API Integration
The app connects to the Tacticus API at `https://api.tacticusgame.com/api/v1/`:
- `GET /player` - Player data (units, inventory, progress)
- `GET /guild` - Guild information (requires Guild scope)
- `GET /guildRaid` - Guild raid data (requires Guild Raid scope)

Authentication uses the `X-API-KEY` header with a UUID token. Users obtain their API key from https://api.tacticusgame.com/.

### Session Management
API keys are stored in Flask session (server-side). The key is validated on entry by making a test request to the player endpoint.

## Key Patterns

- All API calls go through helper functions (`fetch_player_data`, `fetch_guild_data`) that handle authentication and error responses
- Templates use conditional rendering to handle varying API response structures
- Raw JSON data is available via expandable `<details>` sections for debugging
- Rarity-based color coding for units uses CSS classes (`.rarity-common`, `.rarity-legendary`, etc.)
