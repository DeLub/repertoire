"""Tests for database module."""
import pytest
import tempfile
from pathlib import Path

from repertoire.database import Database
from repertoire.models import Composer, Work, Recording, Performer, Label, RecordingType


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    
    yield Database(db_path)
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestComposer:
    """Test composer operations."""
    
    def test_add_composer(self, temp_db):
        """Test adding a composer."""
        composer = Composer(name="Ludwig van Beethoven", birth_year=1770, death_year=1827)
        result = temp_db.add_composer(composer)
        
        assert result.id is not None
        assert result.name == "Ludwig van Beethoven"
    
    def test_get_composer(self, temp_db):
        """Test retrieving a composer."""
        original = Composer(name="Wolfgang Amadeus Mozart", birth_year=1756)
        temp_db.add_composer(original)
        
        retrieved = temp_db.get_composer("Wolfgang Amadeus Mozart")
        assert retrieved is not None
        assert retrieved.name == "Wolfgang Amadeus Mozart"
        assert retrieved.birth_year == 1756
    
    def test_duplicate_composer(self, temp_db):
        """Test that duplicate composers are handled."""
        composer1 = Composer(name="Frédéric Chopin")
        composer2 = Composer(name="Frédéric Chopin")
        
        result1 = temp_db.add_composer(composer1)
        result2 = temp_db.add_composer(composer2)
        
        assert result1.id == result2.id


class TestPerformer:
    """Test performer operations."""
    
    def test_add_performer(self, temp_db):
        """Test adding a performer."""
        performer = Performer(
            name="Itzhak Perlman",
            performer_type="soloist",
            instrument="violin"
        )
        result = temp_db.add_performer(performer)
        
        assert result.id is not None
        assert result.name == "Itzhak Perlman"
        assert result.instrument == "violin"


class TestRecording:
    """Test recording operations."""
    
    def test_add_recording(self, temp_db):
        """Test adding a recording."""
        recording = Recording(
            title="Symphony No. 5 in C minor",
            recording_type=RecordingType.STUDIO,
            catalog_number="DGG-001",
            release_year=2020,
        )
        result = temp_db.add_recording(recording)
        
        assert result.id is not None
        assert result.title == "Symphony No. 5 in C minor"
        assert result.catalog_number == "DGG-001"


class TestQueries:
    """Test database queries."""
    
    def test_get_recordings_empty(self, temp_db):
        """Test querying empty database."""
        recordings = temp_db.get_recordings()
        assert len(recordings) == 0
    
    def test_get_recordings_limit(self, temp_db):
        """Test limit parameter."""
        for i in range(10):
            recording = Recording(title=f"Recording {i}")
            temp_db.add_recording(recording)
        
        recordings = temp_db.get_recordings(limit=5)
        assert len(recordings) == 5
