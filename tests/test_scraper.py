"""Tests for scraper module."""
import pytest
from unittest.mock import Mock, patch

from repertoire.scraper import MusicaliefeitenScraper
from repertoire.parser import extract_text_from_html


class TestMusicaliefeitenScraper:
    """Test scraper functionality."""
    
    def test_scraper_initialization(self):
        """Test scraper can be initialized."""
        scraper = MusicaliefeitenScraper(throttle=0.5)
        assert scraper.throttle == 0.5
        assert scraper.timeout == 10
    
    def test_extract_content_from_html(self):
        """Test extracting text from HTML."""
        html = """
        <article>
            <p>This is a test paragraph about Beethoven.</p>
            <p>He was a great composer.</p>
        </article>
        """
        scraper = MusicaliefeitenScraper()
        paragraphs = scraper.extract_content(html)
        
        assert len(paragraphs) > 0
        assert any("Beethoven" in p for p in paragraphs)
    
    def test_extract_text_from_html(self):
        """Test the parser directly."""
        html = """
        <article>
            <p>First paragraph with content that is long enough.</p>
            <p>Second paragraph also long enough to be extracted.</p>
            <p>X</p>
        </article>
        """
        paragraphs = extract_text_from_html(html)
        
        # Should filter out short paragraphs
        assert len(paragraphs) >= 2
        assert all(len(p) >= 10 for p in paragraphs)
    
    @patch('repertoire.scraper.requests.Session.get')
    def test_scrape_url_success(self, mock_get):
        """Test successful URL scraping."""
        mock_response = Mock()
        mock_response.text = "<html><p>Test content</p></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        scraper = MusicaliefeitenScraper(throttle=0)
        result = scraper.scrape_url("https://example.com")
        
        assert result is not None
        assert "<html>" in result
    
    @patch('repertoire.scraper.requests.Session.get')
    def test_scrape_url_failure(self, mock_get):
        """Test failed URL scraping."""
        from requests import RequestException
        mock_get.side_effect = RequestException("Connection error")
        
        scraper = MusicaliefeitenScraper()
        result = scraper.scrape_url("https://example.com")
        
        assert result is None
