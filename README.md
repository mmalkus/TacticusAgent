# Tacticus Agent

A Flask web application for viewing player data from the Warhammer 40,000: Tacticus mobile game API.

## Features

- **API Key Management**: Securely store your Tacticus API key
- **Player Data**: View account info and raw API response
- **Characters Table**: Sortable table showing all your characters with:
  - Name (links to wiki)
  - Faction (links to wiki)
  - Progression stars with color coding (gold/red/blue/wings)
  - Level and Rank
  - Active and Passive ability levels
  - Upgrade slots (2x3 grid)
  - Shards (including mythic)
- **Guild Data**: View guild information (requires guild scope)
- **Data Caching**: Locally cached data with manual refresh

## Setup

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

You can get your Tacticus API key from the [Tacticus developer portal](https://tacticus.wiki.gg/wiki/API).

## License

MIT
