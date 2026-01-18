# Raycast Extension Development Guide

This directory contains the Raycast extension for Repertoire, which provides:

1. **Scrape musicalifeiten** - Fetch and parse classical music metadata using Raycast AI
2. **Browse Collection** - Open the web UI to view your collection

## Development Setup

### Prerequisites

- macOS or Windows with Raycast installed
- Node.js 16+ and npm
- Repertoire backend running (see root README)

### Installation

```bash
# Install dependencies
npm install

# Start development mode
npm run dev
```

This will load the extension in Raycast. You can then access it with `⌘ Space` and search for the command.

## Configuration

The extension uses preferences to connect to the backend. Set these in Raycast extension preferences:

- **Backend URL** (default: `http://localhost:5000`)
  - Must point to your running Flask backend
  - Used by both commands to communicate with the server

## Commands

### 1. Scrape musicalifeiten

**File:** `src/scrape-musicalifeiten.tsx`

This command:
1. Fetches a random page from [musicalifeiten.nl](https://www.musicalifeiten.nl)
2. Uses **Raycast AI** to extract structured metadata (composers, works, performers, labels)
3. Sends the data to the backend API to save in the database
4. Opens the web UI to show the results

**Workflow:**
```
┌─────────────────────────────────────────────┐
│ Raycast Extension (scrape command)          │
└────────────────────┬────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Fetch HTML  Raycast AI   Parse Response
    from musicalifeiten  (extracts metadata)
        │            │            │
        └────────────┼────────────┘
                     ▼
        ┌─────────────────────────┐
        │ POST /api/recordings    │
        │ Send enriched data      │
        └────────┬────────────────┘
                 ▼
        ┌─────────────────────────┐
        │ Backend (Flask)         │
        │ Save to SQLite          │
        └────────┬────────────────┘
                 ▼
        ┌─────────────────────────┐
        │ Open Web UI             │
        │ View saved recordings   │
        └─────────────────────────┘
```

**Expected JSON Response from Raycast AI:**
```json
[
  {
    "composer": "Ludwig van Beethoven",
    "work": "Symphony No. 5 in C minor",
    "performers": ["Berlin Philharmonic", "Herbert von Karajan"],
    "label": "Deutsche Grammophon",
    "catalogNumber": "439-947-2",
    "releaseYear": 1992,
    "notes": "Complete Symphonies box set"
  }
]
```

### 2. Browse Collection

**File:** `src/browse-collection.ts`

Simple command that opens the web UI in your browser. Lets you:
- Search and filter recordings
- View statistics
- Explore your collection

## How the Integration Works

### Step 1: Fetch HTML
The extension fetches a random page from musicalifeiten.nl:
```typescript
const { data: htmlData } = useFetch("https://www.musicalifeiten.nl/composers/by-name/a/");
```

### Step 2: Process with Raycast AI
The HTML is sent to Raycast AI for processing:
```typescript
const { data: aiResponse } = useAI(`
  Extract classical music recording information...
  ${htmlData}
`);
```

### Step 3: Parse AI Response
The JSON response is parsed and validated:
```typescript
const parsedRecordings = JSON.parse(aiResponse);
```

### Step 4: Save to Backend
Data is sent to the Flask API:
```typescript
const response = await fetch(`${backendUrl}/api/recordings`, {
  method: "POST",
  body: JSON.stringify({ recordings: parsedRecordings })
});
```

### Step 5: Open Web UI
After successful save, the web UI opens automatically:
```typescript
open(`${backendUrl}`);
```

## Debugging

### Check Backend Connection
Make sure the Flask backend is running:
```bash
python -m repertoire.cli server --port 5000
```

### View Raycast Logs
In Raycast, go to:
1. `⌘ Space` → Search "Develop Extension"
2. Select your extension
3. View console output for errors

### Test API Manually
```bash
# Test POST endpoint
curl -X POST http://localhost:5000/api/recordings \
  -H "Content-Type: application/json" \
  -d '{
    "recordings": [
      {
        "composer": "Test Composer",
        "work": "Test Work",
        "performers": ["Test Performer"]
      }
    ]
  }'
```

## File Structure

```
src/
├── scrape-musicalifeiten.tsx    # Main scraper command
├── browse-collection.ts          # Open web UI command
```

## Preferences Schema

The extension declares preferences in `package.json`:

```json
{
  "preferences": [
    {
      "name": "backendUrl",
      "type": "textfield",
      "required": true,
      "title": "Backend URL",
      "default": "http://localhost:5000"
    }
  ]
}
```

Users can modify these in Raycast extension settings.

## Error Handling

The scraper handles several error scenarios:

1. **Network Error** - If musicalifeiten.nl is unreachable
2. **AI Parsing Error** - If Raycast AI produces invalid JSON
3. **Backend Error** - If the API returns an error
4. **JSON Validation** - If parsed data doesn't match expected structure

All errors are shown as toast notifications to the user.

## Building for Distribution

```bash
# Lint code
npm run lint

# Build for distribution
npm run build

# Publish to Raycast Store (if approved)
npm run publish
```

## Testing

While Raycast doesn't have a built-in test framework, you can:

1. Test the TypeScript/React components with manual testing
2. Use `npm run lint` to check for syntax errors
3. Test the API endpoints with curl/Postman

## Performance Considerations

- **Caching**: Raycast AI may cache results for the same prompts
- **Rate Limiting**: musicalifeiten.nl may rate-limit requests
- **Backend**: Make sure Flask is running locally for fastest response

## Future Enhancements

- [ ] Batch scraping (multiple pages at once)
- [ ] Schedule recurring scrapes
- [ ] Edit/delete recordings from extension
- [ ] Advanced search/filtering in detail view
- [ ] Sync with Discogs or other sources

## Troubleshooting

### "Connection refused" error
- Make sure Flask backend is running: `python -m repertoire.cli server`
- Check backend URL in preferences matches actual server address

### "Invalid JSON" error
- Raycast AI output format may have changed
- Try a different prompt or restart the extension

### No recordings appear in web UI
- Check Flask console for errors
- Verify the backend URL is correct
- Check browser console (F12) for JavaScript errors
