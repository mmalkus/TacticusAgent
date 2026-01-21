# Tacticus Agent

A Flask web application for viewing player data from the Warhammer 40,000: Tacticus mobile game API.

## Features

- **Player Data**: View account info including player name, guild, and power level
- **Characters Table**: Sortable table showing all your characters with:
  - Name (links to wiki)
  - Faction (links to wiki)
  - Progression stars with color coding (gold/red/blue/wings)
  - Level and Rank
  - Active and Passive ability levels
  - Upgrade slots (2x3 grid)
  - Shards (including mythic)
- **Guild Data**: View guild information with member list (requires Guild scope)
  - Editable usernames stored locally
  - Sortable member table with role, level
- **Guild Raid**: View raid statistics (requires Guild Raid scope)
  - Damage per boss with min/avg/max/stddev
  - Click on boss for per-player breakdown
  - Sortable tables
- **Data Caching**: Locally cached data with manual refresh
- **API Key Management**: Securely store your Tacticus API key

## Quick Start

### Windows
```batch
install.bat
run.bat
```

### Linux/Mac
```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```

## Manual Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the application:
   ```bash
   python app.py
   ```
6. Open http://localhost:5000 in your browser

## Getting an API Key

Get your Tacticus API key from [api.tacticusgame.com](https://api.tacticusgame.com/). Enable the following scopes:
- **Player** - For player and character data
- **Guild** - For guild member information
- **Guild Raid** - For guild raid statistics

## License

MIT
