# MusicBrainz Integration Guide

Repertoire uses **MusicBrainz** to standardize composer names and work titles. This ensures consistent data across your collection.

## What is MusicBrainz?

[MusicBrainz](https://musicbrainz.org/) is an open music encyclopedia that collects information about:
- **Artists** (composers, conductors, orchestras)
- **Works** (symphonies, concertos, operas)
- **Recordings** (albums, tracks, performances)

MusicBrainz IDs provide a canonical reference for classical music entities.

## How Repertoire Uses It

### 1. Composer Name Standardization

When a composer is added to your database, Repertoire automatically:
1. Searches MusicBrainz for the composer
2. Retrieves the canonical name and birth/death years
3. Stores the MusicBrainz ID for future reference

**Example:**
```
Input:  "W.A. Mozart"
MusicBrainz: "Wolfgang Amadeus Mozart" (1756-1791)
Stored as: "Wolfgang Amadeus Mozart" with MB ID
```

### 2. Work Title Standardization

Similarly for works:
```
Input:  "Symphony No. 5 in C minor"
MusicBrainz: "Symphony No. 5 in C minor, Op. 67" (Beethoven)
Stored with: MB ID and catalog information
```

## Configuration

### Get a MusicBrainz Account (Optional)

While not required, having an account allows higher rate limits:

1. Visit [musicbrainz.org](https://musicbrainz.org/)
2. Click "Register"
3. Create an account
4. Go to Settings → API
5. Generate an API token if available

### Set Environment Variable

```bash
# In your .env file
MUSICBRAINZ_API_KEY=your_api_key_here
```

If not set, the integration will still work with public access (rate-limited to ~1 request per second).

## Usage in Code

### From Python Backend

```python
from repertoire.musicbrainz import MusicBrainzIntegration

mb = MusicBrainzIntegration()

# Standardize a composer name
canonical_name = mb.standardize_composer_name("Ludwig van Beethoven")
# Returns: "Ludwig van Beethoven"

# Get full artist info
artist_info = mb.search_artist("Mozart")
# Returns: {
#     "mb_id": "69c86....",
#     "name": "Wolfgang Amadeus Mozart",
#     "sort_name": "Mozart, Wolfgang Amadeus",
#     "birth_year": 1756,
#     "death_year": 1791,
#     "country": "AT"
# }

# Standardize a work title
canonical_title = mb.standardize_work_title("Sym 5", "Beethoven")
# Returns: "Symphony No. 5 in C minor, Op. 67"
```

### From Raycast Extension

Currently, the Raycast extension sends composer and work names to Raycast AI, which processes them. The backend can then:

1. Receive the parsed composer/work names
2. Look them up in MusicBrainz
3. Store the standardized versions with MB IDs

### CLI Integration

```bash
# Future: Standardize all existing data
python -m repertoire.cli standardize --composer

# Enrich with MusicBrainz data
python -m repertoire.cli enrich-musicbrainz --all
```

## Database Schema

The MusicBrainz integration adds these fields:

**Composers Table:**
```sql
musicbrainz_id TEXT UNIQUE  -- MusicBrainz artist ID
```

**Works Table:**
```sql
musicbrainz_id TEXT UNIQUE  -- MusicBrainz work ID
```

These allow future lookups and prevent duplicate entries.

## API Methods

### search_artist(name, artist_type="Person")

Search for a composer or performer.

```python
result = mb.search_artist("Beethoven")
# {
#   "mb_id": "...",
#   "name": "Ludwig van Beethoven",
#   "sort_name": "Beethoven, Ludwig van",
#   "type": "Person",
#   "country": "DE",
#   "life_span": {"begin": "1770-12-17", "end": "1827-03-26"}
# }
```

### search_work(title, composer_name=None)

Search for a musical work.

```python
result = mb.search_work("Symphony No. 5", "Beethoven")
# {
#   "mb_id": "...",
#   "title": "Symphony No. 5 in C minor, Op. 67",
#   "type": "Symphony",
#   "composer": {...}
# }
```

### get_artist_info(mb_id)

Get detailed info for an artist by MusicBrainz ID.

```python
result = mb.get_artist_info("1f9df192-a621-4f12-8350-85394dc4c437")
```

### standardize_composer_name(name)

Quick method to get just the standardized name.

```python
canonical = mb.standardize_composer_name("W.A. Mozart")
# Returns: "Wolfgang Amadeus Mozart"
```

### standardize_work_title(title, composer_name=None)

Quick method to get just the standardized work title.

```python
canonical = mb.standardize_work_title("Symphony 5", "Beethoven")
# Returns: "Symphony No. 5 in C minor, Op. 67"
```

## Performance Considerations

### Caching

The integration uses `@lru_cache` for performance:

```python
@lru_cache(maxsize=256)
def search_artist(self, name: str, artist_type: str = "Person"):
    # Results are cached - same query won't hit MusicBrainz twice
```

This means:
- First lookup: ~200ms (network request)
- Subsequent lookups: <1ms (cache)

### Rate Limiting

MusicBrainz has rate limits:
- **Without API key**: ~1 request/second
- **With API key**: ~1 request/second (but more reliable)

The integration respects these limits automatically.

## Error Handling

All MusicBrainz methods gracefully handle errors:

```python
result = mb.search_artist("Invalid (Name []")
# Returns None instead of crashing
```

Errors are logged to console but won't break the scraping process.

## Testing

Run the MusicBrainz tests:

```bash
pytest tests/test_musicbrainz.py -v
```

Tests use mocked HTTP responses, so they don't make real API calls.

## Future Enhancements

- [ ] Batch lookup (multiple artists at once)
- [ ] Fuzzy matching for typo tolerance
- [ ] Store MB data in cache for offline use
- [ ] Discogs integration for cover art
- [ ] Wikipedia links for composers
- [ ] Recording metadata from MB

## Troubleshooting

### "Connection error" to MusicBrainz

**Problem:** Can't reach MusicBrainz API

**Solutions:**
1. Check internet connection
2. MusicBrainz may be temporarily down - try again later
3. Check rate limiting - slow down requests

### "No results found"

**Problem:** Composer/work not found in MusicBrainz

**Solutions:**
1. MusicBrainz might use different spelling
2. Try searching without special characters
3. Contribute to MusicBrainz if it's missing (it's crowdsourced!)

### Slow performance

**Problem:** Lookups taking >1 second

**Solutions:**
1. Cache is working but first-time lookups are slow - this is normal
2. Check internet connection speed
3. Reduce batch operations

## Resources

- [MusicBrainz API Docs](https://musicbrainz.org/doc/Development/API)
- [MusicBrainz Entity Types](https://musicbrainz.org/doc/Entity)
- [Entity IDs](https://musicbrainz.org/doc/Identities_and_Relationships)
- [Relationship Types](https://musicbrainz.org/relationships)

## Examples

### Add a recording with MusicBrainz lookup

```python
from repertoire.musicbrainz import MusicBrainzIntegration
from repertoire.database import Database
from repertoire.models import Composer, Work, Recording

mb = MusicBrainzIntegration()
db = Database("repertoire.db")

# Get standardized composer
composer_info = mb.search_artist("Beethoven")
composer = Composer(
    name=composer_info["name"],
    birth_year=1770,
    death_year=1827,
    musicbrainz_id=composer_info["mb_id"]
)
composer = db.add_composer(composer)

# Get standardized work
work_info = mb.search_work("Symphony No. 5", "Beethoven")
work = Work(
    composer_id=composer.id,
    title=work_info["title"],
    musicbrainz_id=work_info["mb_id"]
)

# Add recording
recording = Recording(
    title="Symphony No. 5 in C minor",
    release_year=1992
)
db.add_recording(recording)
```

This ensures all your data is standardized against the MusicBrainz database.
