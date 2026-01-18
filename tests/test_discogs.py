"""Tests for Discogs integration."""
import pytest
from unittest.mock import Mock, patch

from repertoire.discogs import DiscogsClient, DiscogsRelease


class TestDiscogsClient:
    """Test Discogs API integration."""
    
    @pytest.fixture
    def client(self):
        """Create a Discogs client for testing."""
        return DiscogsClient(token="test_token")

    def test_extract_release_id_from_url(self, client):
        """Test extracting release ID from various Discogs URLs."""
        urls = [
            ("https://www.discogs.com/release/123456", "123456"),
            ("http://discogs.com/release/789", "789"),
            ("discogs.com/Something/release/999", "999"),
            ("invalid-url.com", None),
        ]

        for url, expected_id in urls:
            assert client.extract_release_id(url) == expected_id

    @patch('repertoire.discogs.requests.Session.get')
    def test_get_release_success(self, mock_get):
        """Test fetching a release by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123456,
            "title": "Symphony No. 5",
            "country": "Germany",
            "released": "1992-01-01",
            "labels": [{"name": "Deutsche Grammophon", "catno": "439-947-2"}],
            "images": [{"type": "primary", "uri": "https://example.com/cover.jpg"}],
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = DiscogsClient(token="test")
        release = client.get_release("123456")

        assert release is not None
        assert release.release_id == "123456"
        assert release.title == "Symphony No. 5"
        assert release.label_name == "Deutsche Grammophon"
        assert release.catalog_number == "439-947-2"

    @patch('repertoire.discogs.requests.Session.get')
    def test_get_release_not_found(self, mock_get):
        """Test handling of missing release."""
        mock_get.side_effect = Exception("404 Not Found")

        client = DiscogsClient(token="test")
        release = client.get_release("invalid")

        assert release is None

    @patch('repertoire.discogs.requests.Session.get')
    def test_find_release_by_catalog(self, mock_get):
        """Test finding release by catalog number."""
        search_response = {
            "results": [
                {
                    "id": 123456,
                    "title": "Symphony No. 5",
                    "catno": "439-947-2",
                    "label": ["Deutsche Grammophon"],
                    "country": "Germany",
                }
            ]
        }
        
        release_response = {
            "id": 123456,
            "title": "Symphony No. 5",
            "country": "Germany",
            "labels": [{"name": "Deutsche Grammophon", "catno": "439-947-2"}],
            "images": [],
        }

        mock_get.side_effect = [
            Mock(json=lambda: search_response, raise_for_status=Mock()),
            Mock(json=lambda: release_response, raise_for_status=Mock()),
        ]

        client = DiscogsClient(token="test")
        release = client.find_release(catalog_number="439-947-2", label="Deutsche Grammophon")

        assert release is not None
        assert release.title == "Symphony No. 5"

    def test_normalize_catalog(self):
        """Test catalog number normalization."""
        assert DiscogsClient._normalize_catalog("DGG 439-947-2") == "DGG4399472"
        assert DiscogsClient._normalize_catalog("439.947.2") == "4399472"
        assert DiscogsClient._normalize_catalog("DGG-439-947-2") == "DGG4399472"

    def test_extract_ean(self):
        """Test EAN extraction."""
        release = {
            "identifiers": [
                {"type": "barcode", "value": "028941394726"}
            ]
        }
        ean = DiscogsClient._extract_ean(release)
        assert ean == "028941394726"

    def test_extract_ean_too_short(self):
        """Test that short barcodes are rejected."""
        release = {
            "identifiers": [
                {"type": "barcode", "value": "123"}  # Too short
            ]
        }
        ean = DiscogsClient._extract_ean(release)
        assert ean is None

    def test_extract_year(self):
        """Test year extraction."""
        assert DiscogsClient._extract_year({"released": "1992-01-15"}) == "1992"
        assert DiscogsClient._extract_year({"year": 2020}) == "2020"
        assert DiscogsClient._extract_year({}) is None

    def test_choose_best_result(self):
        """Test selection of best search result."""
        results = [
            {"id": 1, "catno": "DGG-1", "label": ["Other Label"], "country": "USA"},
            {"id": 2, "catno": "DGG-2", "label": ["Deutsche Grammophon"], "country": "Germany"},
            {"id": 3, "catno": "DGG-2", "label": ["Deutsche Grammophon"], "country": "Netherlands"},
        ]

        # Best should be result with matching catno, label, and Netherlands/Europe location
        best = DiscogsClient._choose_best_result(
            results,
            label="Deutsche Grammophon",
            catalog_number="DGG-2"
        )
        
        assert best["id"] == 3  # Netherlands preferred over Germany

    def test_discogsrelease_dataclass(self):
        """Test DiscogsRelease dataclass."""
        release = DiscogsRelease(
            release_id="123",
            title="Test Release",
            year="2020",
            ean="028941394726",
            label_name="Test Label",
        )

        assert release.release_id == "123"
        assert release.title == "Test Release"
        assert release.year == "2020"
