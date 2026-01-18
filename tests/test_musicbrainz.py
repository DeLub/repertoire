"""Tests for MusicBrainz integration."""
import pytest
from unittest.mock import Mock, patch

from repertoire.musicbrainz import MusicBrainzIntegration


class TestMusicBrainzIntegration:
    """Test MusicBrainz API integration."""
    
    def test_initialization(self):
        """Test MusicBrainzIntegration can be initialized."""
        mb = MusicBrainzIntegration()
        assert mb.timeout == 10
        assert mb.session is not None
    
    @patch('repertoire.musicbrainz.requests.Session.get')
    def test_search_artist_success(self, mock_get):
        """Test successful artist search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "artists": [
                {
                    "id": "1f9df192-a621-4f12-8350-85394dc4c437",
                    "name": "Ludwig van Beethoven",
                    "sort-name": "Beethoven, Ludwig van",
                    "type": "Person",
                    "country": "DE",
                    "life-span": {
                        "begin": "1770-12-17",
                        "end": "1827-03-26"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        mb = MusicBrainzIntegration()
        result = mb.search_artist("Ludwig van Beethoven")
        
        assert result is not None
        assert result["name"] == "Ludwig van Beethoven"
        assert result["sort_name"] == "Beethoven, Ludwig van"
        assert result["mb_id"] == "1f9df192-a621-4f12-8350-85394dc4c437"
    
    @patch('repertoire.musicbrainz.requests.Session.get')
    def test_search_artist_not_found(self, mock_get):
        """Test artist not found."""
        mock_response = Mock()
        mock_response.json.return_value = {"artists": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        mb = MusicBrainzIntegration()
        result = mb.search_artist("Nonexistent Composer")
        
        assert result is None
    
    @patch('repertoire.musicbrainz.requests.Session.get')
    def test_search_work_success(self, mock_get):
        """Test successful work search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "works": [
                {
                    "id": "dfe4e4f5-e2e6-4d27-95a2-d43a85e1bc50",
                    "title": "Symphony No. 5",
                    "type": "Symphony",
                    "language": "en",
                    "relations": []
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        mb = MusicBrainzIntegration()
        result = mb.search_work("Symphony No. 5")
        
        assert result is not None
        assert result["title"] == "Symphony No. 5"
        assert result["type"] == "Symphony"
    
    @patch('repertoire.musicbrainz.requests.Session.get')
    def test_standardize_composer_name(self, mock_get):
        """Test getting standardized composer name."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "artists": [
                {
                    "id": "1f9df192-a621-4f12-8350-85394dc4c437",
                    "name": "Wolfgang Amadeus Mozart",
                    "sort-name": "Mozart, Wolfgang Amadeus",
                    "type": "Person",
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        mb = MusicBrainzIntegration()
        name = mb.standardize_composer_name("W.A. Mozart")
        
        assert name == "Wolfgang Amadeus Mozart"
    
    @patch('repertoire.musicbrainz.requests.Session.get')
    def test_caching(self, mock_get):
        """Test that results are cached."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "artists": [
                {
                    "id": "test-id",
                    "name": "Test Composer",
                    "sort-name": "Composer, Test",
                    "type": "Person",
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        mb = MusicBrainzIntegration()
        
        # Call twice
        mb.search_artist("Test Composer")
        mb.search_artist("Test Composer")
        
        # Should only make one HTTP request due to caching
        assert mock_get.call_count == 1
