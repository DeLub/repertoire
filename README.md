# Repertoire

**Classical music manager with AI-powered metadata enrichment using Raycast AI.**

A full-stack application that lets you scrape, organize, and explore your classical music collection. Combines a Python backend with a Raycast extension frontend and Flask web UI.

## Features

✨ **Core Features**
- 🔗 Scrape classical music metadata from [musicalifeiten.nl](https://www.musicalifeiten.nl)
- 🎼 Organize by composer, work, performer, and recording
- 🤖 AI-powered metadata enrichment using Raycast AI (instead of OpenAI)
- 💿 Discogs integration for covers, catalog numbers, and EANs
- 📚 SQLite database for persistent storage
- 🌐 Web UI with search and filtering
- 📱 Raycast extension for quick access and scraping from your desktop

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Raycast installed (for the extension)
- **No API keys required** - Raycast AI is built-in to Raycast itself

### Backend Setup

**1. Create Python virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**2. Install dependencies**
```bash
pip install -e ".[dev]"
```

**3. Create environment file (optional)**
```bash
cat > .env << EOF
REPERTOIRE_DB_PATH=repertoire.db
DISCOGS_TOKEN=your_discogs_token_here  # Optional, for cover art
EOF
```

**Note:** No RAYCAST_AI_KEY needed - Raycast AI is handled entirely by the extension itself!

### Running the Application

**Web UI + Backend**
```bash
python -m repertoire.cli server --port 5000
```
Then open [http://localhost:5000](http://localhost:5000) in your browser.

**Raycast Extension**
```bash
npm install
npm run dev
```

## Workflow: Scraping and Adding to Database

### From Raycast Extension
1. Open Raycast (`⌘ Space`)
2. Search for "Scrape musicalifeiten"
3. Select the command
4. The Raycast AI will process a random page
5. Results are sent to the backend server and saved to database

### From Command Line
```bash
# Scrape one random page
python -m repertoire.cli scrape --pages 1

# Query what was added
python -m repertoire.cli query --composer Beethoven
```

## API Endpoints

- `GET /` - Web UI
- `GET /api/recordings` - Query recordings
- `GET /api/stats` - Database statistics

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=repertoire
```

## License

MIT