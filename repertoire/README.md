# Repertoire Backend Python Package

This is the Python backend for Repertoire. It handles:
- Database management (SQLite)
- Web scraping from musicalifeiten.nl
- AI-powered metadata enrichment using Raycast AI
- Discogs integration for covers and catalog information
- CLI commands
- Web UI (Flask)

## Development Setup

### 1. Create and activate virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -e ".[dev]"
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run tests
```bash
pytest
```

### 5. Start development
```bash
# Run the scraper
python -m repertoire.cli scrape --help

# Start the web server
python -m webui.app
```

## Project Structure

- `repertoire/` - Core Python package
  - `database.py` - SQLite database models and queries
  - `models.py` - Data models (Composer, Work, Recording, etc.)
  - `scraper.py` - musicalifeiten.nl scraper
  - `parser.py` - HTML parsing logic
  - `llm.py` - Raycast AI integration
  - `discogs.py` - Discogs API integration
  - `cli.py` - Command-line interface
  - `progress.py` - Scrape progress tracking
  
- `webui/` - Flask web application
  - `app.py` - Web server and routes
  - `templates/` - HTML templates
  - `static/` - CSS/JS assets

- `tests/` - Pytest test suite
  - `test_scraper.py` - Scraper tests
  - `test_database.py` - Database tests
  - `test_parser.py` - Parser tests

## Environment Variables

```
REPERTOIRE_DB_PATH=repertoire.db          # Path to SQLite database
RAYCAST_AI_URL=http://localhost:5000      # Raycast AI backend URL
DISCOGS_TOKEN=your_token                  # Discogs API token
REPERTOIRE_CACHE_DIR=~/.cache/repertoire  # Cache directory for progress/LLM responses
```
